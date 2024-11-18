import json
import logging
import time
from typing import Tuple, Optional
from django.conf import settings
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

logger = logging.getLogger(__name__)

class LLMServiceException(Exception):
    """Base exception for LLM service errors"""
    pass

class LLMConnectionError(LLMServiceException):
    """Raised when there are connection/network issues"""
    pass

class LLMResponseError(LLMServiceException):
    """Raised when the LLM response is invalid"""
    pass

class LLMService:
    # Maximum retries for API calls
    MAX_RETRIES = 3
    # Initial delay between retries (in seconds)
    INITIAL_RETRY_DELAY = 1
    # Maximum delay between retries (in seconds)
    MAX_RETRY_DELAY = 10

    @staticmethod
    def clean_json_output(output: str) -> str:
        """Extract only the JSON part from the LLM output"""
        try:
            output = output.replace("```json", "").replace("```", "")
            
            start = output.find('{')
            end = output.rfind('}') + 1
            
            if start >= 0 and end > 0:
                potential_json = output[start:end]
                
                # Try to parse it to validate
                json.loads(potential_json)
                return potential_json
                
            raise LLMResponseError("No JSON object found in output")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e}")
            logger.error(f"Raw output: {output}")
            raise LLMResponseError(f"Invalid JSON format: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error cleaning JSON: {e}")
            logger.error(f"Raw output: {output}")
            raise LLMResponseError(f"Failed to process output: {str(e)}")

    @staticmethod
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY, max=MAX_RETRY_DELAY),
        retry=retry_if_exception_type((httpx.HTTPError, LLMConnectionError)),
        before_sleep=lambda retry_state: logger.info(
            f"Retrying LLM request after {retry_state.outcome.exception()}, "
            f"attempt {retry_state.attempt_number}"
        )
    )
    def _make_llm_request(prompt_messages: list, model: str = "llama3-groq-70b-8192-tool-use-preview") -> Tuple[bool, str, Optional[str]]:
        """Make the actual LLM API request with retry logic"""
        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            response = client.chat.completions.create(
                model=model,
                messages=prompt_messages,
                temperature=0.1,
                max_tokens=2000,
                top_p=0.9
            )
            
            return True, response.choices[0].message.content, None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during LLM request: {e}")
            return False, None, f"Connection error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during LLM request: {e}")
            return False, None, f"LLM service error: {str(e)}"

    @classmethod
    def generate_product_tree(cls, product_name: str, product_description: str, additional_context: str = "") -> Tuple[bool, str, Optional[str]]:
        """Generate a product tree structure using LLM"""
        prompt_messages = [{
            "role": "system",
            "content": """You are a product strategist creating intuitive product trees that focus on user journeys and business value.
Think about the key paths users take to achieve their goals."""
        }, {
            "role": "user", 
            "content": f"""Create a product tree that shows how users experience and interact with {product_name}.

Product Description: {product_description}

Key Principles:
1. Start with key user journeys:
   - Discovery: How users find what they need
   - Core Value: Main activities users perform
   - Growth: How users progress and develop

2. Think about:
   - User goals and motivations
   - Natural progression through activities
   - Value creation and capture
   - Key decision points

3. Use these lenses naturally:
   - Experience-based: Main user journeys
   - Flow-based: Important processes
   - Persona-based: Different user needs
   - Feature-based: Only for specific capabilities

4. Structure using this schema:
{{
    "name": "Journey/Area name",
    "description": "User goals and value (2-3 sentences)",
    "lens_type": "experience|flow|persona|feature",
    "children": []
}}

5. Focus on:
   - Natural user progression
   - Value delivery points
   - Key user decisions
   - Growth opportunities

Additional Context:
{additional_context}

Return only a valid JSON object."""
        }]

        try:
            # Make LLM request with retry logic
            success, content, error = cls._make_llm_request(prompt_messages)
            if not success:
                return False, "", error
            
            # Clean and validate JSON response
            json_str = cls.clean_json_output(content)
            return True, json_str, None

        except LLMConnectionError as e:
            logger.error(f"Failed to connect to LLM service: {e}")
            return False, "", f"Service temporarily unavailable: {str(e)}"
            
        except LLMResponseError as e:
            logger.error(f"Invalid LLM response: {e}")
            return False, "", f"Failed to generate valid tree structure: {str(e)}"
            
        except LLMServiceException as e:
            logger.error(f"LLM service error: {e}")
            return False, "", f"Service error: {str(e)}"
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, "", f"Unexpected error: {str(e)}"

    @classmethod
    def refine_product_tree(cls, current_tree: str, feedback: str, product_name: str) -> Tuple[bool, str, Optional[str]]:
        """Refine an existing product tree based on feedback"""
        prompt_messages = [{
            "role": "system",
            "content": """You are a product strategist helping to refine and improve product trees.
Focus on incorporating feedback while maintaining the existing structure and format."""
        }, {
            "role": "user",
            "content": f"""Refine this product tree for {product_name} based on the provided feedback.

Current Tree:
{current_tree}

Feedback to incorporate:
{feedback}

Keep the same JSON schema:
{{
    "name": "Journey/Area name",
    "description": "User goals and value (2-3 sentences)",
    "lens_type": "experience|flow|persona|feature",
    "children": []
}}

Return only a valid JSON object with the refined tree."""
        }]

        try:
            # Make LLM request with retry logic
            success, content, error = cls._make_llm_request(prompt_messages)
            if not success:
                return False, "", error
            
            # Clean and validate JSON response
            json_str = cls.clean_json_output(content)
            return True, json_str, None

        except LLMConnectionError as e:
            logger.error(f"Failed to connect to LLM service: {e}")
            return False, "", f"Service temporarily unavailable: {str(e)}"
            
        except LLMResponseError as e:
            logger.error(f"Invalid LLM response: {e}")
            return False, "", f"Failed to generate valid tree structure: {str(e)}"
            
        except LLMServiceException as e:
            logger.error(f"LLM service error: {e}")
            return False, "", f"Service error: {str(e)}"
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, "", f"Unexpected error: {str(e)}"
