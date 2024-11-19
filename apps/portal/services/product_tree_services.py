from typing import Tuple, Optional, Dict, Any
from apps.capabilities.product_management.models import Product
from .ai_services import LLMService
import json
import logging

logger = logging.getLogger(__name__)

class ProductTreeService:
    def generate_initial_tree(self, product: Product, additional_context: str = "") -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Generate initial product tree using LLM.
        Returns: (success, tree_dict, error_message)
        """
        logger.debug("Starting generate_initial_tree", extra={
            'product_name': product.name,
            'additional_context': additional_context
        })
        
        try:
            success, tree_json_str, error = LLMService.generate_product_tree(
                product_name=product.name,
                product_description=product.short_description,
                additional_context=additional_context
            )
            
            logger.debug("LLM response", extra={
                'success': success,
                'tree_json_str': tree_json_str,
                'error': error
            })
            
            if not success:
                return False, None, error
                
            # Parse JSON string into Python dict
            tree_dict = json.loads(tree_json_str)
            logger.debug("Initial parsed tree_dict", extra={'tree_dict': tree_dict})
            
            def validate_and_preserve_tree(node, path="root"):
                """Recursively validate while preserving all data"""
                logger.debug(f"Validating node at {path}", extra={'input_node': node})
                
                if not isinstance(node, dict):
                    logger.error(f"Invalid node at {path}", extra={'node': node})
                    raise ValueError(f"Invalid node structure at {path}")
                
                # Ensure required fields exist but don't modify existing data
                validated_node = {
                    'name': str(node.get('name', '')),
                    'description': str(node.get('description', '')),
                    'lens_type': str(node.get('lens_type', 'experience')),
                    'children': []
                }
                
                # Preserve existing children
                if 'children' in node:
                    validated_node['children'] = [
                        validate_and_preserve_tree(child, f"{path}.children[{i}]")
                        for i, child in enumerate(node['children'])
                    ]
                    logger.debug(f"Processed children at {path}", extra={
                        'children_count': len(validated_node['children']),
                        'children': validated_node['children']
                    })
                
                logger.debug(f"Validated node at {path}", extra={
                    'input_node': node,
                    'validated_node': validated_node
                })
                return validated_node
            
            # Validate while preserving structure
            validated_tree = validate_and_preserve_tree(tree_dict)
            logger.debug("Final validated tree", extra={'tree': validated_tree})
            
            return True, validated_tree, None
            
        except json.JSONDecodeError as e:
            logger.error("JSON decode error", extra={'error': str(e), 'tree_json_str': tree_json_str})
            return False, None, f"Invalid tree structure: {str(e)}"
        except Exception as e:
            logger.error("Unexpected error", extra={'error': str(e)})
            return False, None, str(e)

    def refine_tree(self, product: Product, current_tree: Dict[str, Any], feedback: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Refine existing tree based on feedback.
        Returns: (success, refined_tree_dict, error_message)
        """
        try:
            # Convert current_tree dict to JSON string for LLM
            current_tree_json = json.dumps(current_tree)
            
            success, refined_json_str, error = LLMService.refine_product_tree(
                current_tree=current_tree_json,
                feedback=feedback,
                product_name=product.name
            )
            
            if not success:
                return False, None, error
                
            # Parse refined JSON string into Python dict
            refined_dict = json.loads(refined_json_str)
            return True, refined_dict, None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse refined tree JSON: {e}")
            return False, None, f"Invalid tree structure: {str(e)}"
        except Exception as e:
            logger.error(f"Failed to refine tree: {e}")
            return False, None, str(e)

    def save_tree(self, product: Product, tree: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Save the generated tree to the database.
        Returns: (success, error_message)
        """
        try:
            # Convert dict to JSON string for storage if needed
            tree_json = json.dumps(tree)
            # Implement actual storage logic here
            # For now, this is a placeholder
            return True, None
        except Exception as e:
            logger.error(f"Failed to save tree: {e}")
            return False, str(e)

    def get_tree(self, product: Product) -> Optional[Dict[str, Any]]:
        """
        Retrieve the saved tree for a product.
        Returns: The tree as a Python dict or None if not found
        """
        try:
            # Implement actual retrieval logic here
            # When implemented, remember to parse JSON string to dict
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve tree: {e}")
            return None
