from typing import Tuple, Optional
from apps.capabilities.product_management.models import Product
from .ai_services import LLMService
from .portal_services import ProductTreeGenerationService

class ProductTreeService:
    def generate_initial_tree(self, product: Product, additional_context: str = "") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate initial product tree using LLM.
        Returns: (success, tree_text, error_message)
        """
        try:
            service = ProductTreeGenerationService()
            return service.generate_initial_tree(product, additional_context)
        except Exception as e:
            return False, None, str(e)

    def refine_tree(self, product: Product, current_tree: str, feedback: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Refine existing tree based on feedback.
        Returns: (success, refined_tree_text, error_message)
        """
        try:
            service = ProductTreeGenerationService()
            return service.refine_tree(product, current_tree, feedback)
        except Exception as e:
            return False, None, str(e)

    def save_tree(self, product: Product, tree: str) -> Tuple[bool, Optional[str]]:
        """
        Save the generated tree to the database.
        Returns: (success, error_message)
        """
        try:
            service = ProductTreeGenerationService()
            return service.save_tree(product, tree)
        except Exception as e:
            return False, str(e)

    def get_tree(self, product: Product) -> Optional[str]:
        """
        Retrieve the saved tree for a product.
        Returns: The tree JSON string or None if not found
        """
        try:
            service = ProductTreeGenerationService()
            return service.get_tree(product)
        except Exception as e:
            logger.error(f"Error retrieving tree: {e}")
            return None
