import json
import logging
import time
from typing import Tuple, Optional
from django.conf import settings
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

print("=== AI Services module loading ===")
print(f"Module path: {__file__}")
logger = logging.getLogger(__name__)
print(f"Logger name: {__name__}")

logger.info("AI Services module loaded")

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
        """Extract only the JSON part from the LLM output and ensure it's a plain dict"""
        logger.debug("Starting clean_json_output", extra={'input_data': output})
        try:
            # Clean up the output
            output = output.replace("```json", "").replace("```", "")
            
            start = output.find('{')
            end = output.rfind('}') + 1
            
            if start >= 0 and end > 0:
                potential_json = output[start:end]
                logger.debug("Extracted JSON", extra={'extracted_json': potential_json})
                
                # Parse to validate
                parsed_dict = json.loads(potential_json)
                logger.debug("Initial parsed dict", extra={'parsed_dict': parsed_dict})
                
                # Preserve the exact structure without modification
                # Just ensure all required fields exist
                def ensure_required_fields(node):
                    if not isinstance(node, dict):
                        return node
                    
                    result = {
                        'name': str(node.get('name', '')),
                        'description': str(node.get('description', '')),
                        'lens_type': str(node.get('lens_type', 'experience')),
                        'children': [
                            ensure_required_fields(child) 
                            for child in node.get('children', [])
                        ] if 'children' in node else []
                    }
                    return result
                
                # Process the tree while preserving all children
                processed_dict = ensure_required_fields(parsed_dict)
                logger.debug("Processed dict with preserved structure", extra={'processed_dict': processed_dict})
                
                # Convert back to JSON string
                result = json.dumps(processed_dict)
                logger.debug("Final JSON string", extra={'result': result})
                return result
                
            raise LLMResponseError("No JSON object found in output")
            
        except Exception as e:
            logger.error(f"Error in clean_json_output: {e}", extra={'input': output})
            raise

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

    @staticmethod
    def _convert_to_plain_dict(tree_dict: dict) -> dict:
        """Convert a potentially proxy dict into a plain dict with proper string conversion."""
        return {
            'name': str(tree_dict.get('name', '')),
            'description': str(tree_dict.get('description', '')),
            'lens_type': str(tree_dict.get('lens_type', 'experience')),
            'children': [
                LLMService._convert_to_plain_dict(child)
                for child in tree_dict.get('children', [])
            ]
        }

    @classmethod
    def generate_product_tree(cls, product_name: str, product_description: str, additional_context: str = "") -> Tuple[bool, str, Optional[str]]:
        """Generate initial product tree structure."""
        print("=== Starting generate_product_tree ===")  # Debug print
        print(f"Product name: {product_name}")          # Debug print
        logger.info(f"Starting generate_product_tree for product: {product_name}")
        
        prompt_messages = [{
            "role": "system",
            "content": """You are a product strategist creating intuitive product trees that focus on user journeys and business value.
Think about the key paths users take to achieve their goals."""
        }, {
            "role": "user", 
            "content": f"""Create a product tree that shows how users experience and interact with {product_name}.

Please return the response as a JSON object with this structure:
{{
    "name": "Journey/Area name",
    "description": "Description",
    "lens_type": "experience",
    "children": []
}}"""
        }]
        
        print("=== Making LLM request ===")  # Debug print
        success, content, error = cls._make_llm_request(prompt_messages)
        print(f"Success: {success}")         # Debug print
        print(f"Content: {content}")         # Debug print
        print(f"Error: {error}")            # Debug print
        
        try:
            if not success:
                print(f"LLM request failed: {error}")  # Debug print
                return False, "", error
            
            print("=== Raw LLM response ===")  # Debug print
            print(content)                     # Debug print
            
            json_str = cls.clean_json_output(content)
            tree_dict = json.loads(json_str)
            plain_dict = cls._convert_to_plain_dict(tree_dict)
            
            return True, json.dumps(plain_dict), None

        except Exception as e:
            print(f"=== Error in generate_product_tree ===")  # Debug print
            print(f"Error: {str(e)}")                        # Debug print
            return False, "", f"Unexpected error: {str(e)}"

    @classmethod
    def refine_product_tree(cls, current_tree: str, feedback: str, product_name: str) -> Tuple[bool, str, Optional[str]]:
        """Refine an existing product tree based on feedback"""
        print("=== Starting refine_product_tree ===")  # Debug print
        print(f"Product name: {product_name}")          # Debug print
        logger.info(f"Starting refine_product_tree for product: {product_name}")
        
        prompt_messages = [{
            "role": "system",
            "content": """You are a product strategist creating intuitive product trees that focus on user journeys and business value.
Think about the key paths users take to achieve their goals."""
        }, {
            "role": "user", 
            "content": f"""Refine this product tree based on the feedback while maintaining its structure.

Current Tree:
{current_tree}

Feedback:
{feedback}

Please return the response as a JSON object with this structure:
{{
    "name": "Journey/Area name",
    "description": "Description",
    "lens_type": "experience",
    "children": []
}}"""
        }]
        
        print("=== Making LLM request ===")  # Debug print
        success, content, error = cls._make_llm_request(prompt_messages)
        print(f"Success: {success}")         # Debug print
        print(f"Content: {content}")         # Debug print
        print(f"Error: {error}")            # Debug print
        
        try:
            if not success:
                print(f"LLM request failed: {error}")  # Debug print
                return False, "", error
            
            print("=== Raw LLM response ===")  # Debug print
            print(content)                     # Debug print
            
            json_str = cls.clean_json_output(content)
            tree_dict = json.loads(json_str)
            plain_dict = cls._convert_to_plain_dict(tree_dict)
            
            return True, json.dumps(plain_dict), None

        except Exception as e:
            print(f"=== Error in refine_product_tree ===")  # Debug print
            print(f"Error: {str(e)}")                        # Debug print
            return False, "", f"Unexpected error: {str(e)}"
