from django.core.management.base import BaseCommand
from apps.portal.services.portal_services import ProductTreeGenerationService
from apps.capabilities.product_management.models import Product
import json

class Command(BaseCommand):
    help = 'Generates a product tree'

    def add_arguments(self, parser):
        parser.add_argument('product_id', type=int, help='ID of the product')
        parser.add_argument('--context-file', type=str, help='Path to additional context file')

    def handle(self, *args, **options):
        try:
            product = Product.objects.get(id=options['product_id'])
            
            # Load additional context if provided
            additional_context = ""
            if options['context_file']:
                with open(options['context_file'], 'r') as f:
                    additional_context = f.read()
            
            service = ProductTreeGenerationService()
            success, tree_str, error = service.generate_initial_tree(
                product,
                additional_context=additional_context
            )
            
            if success and tree_str:
                tree = json.loads(tree_str)
                self.stdout.write(json.dumps(tree, indent=2))
            else:
                self.stderr.write(f"Error: {error}")
                
        except Product.DoesNotExist:
            self.stderr.write(f"Product with ID {options['product_id']} not found")
        except Exception as e:
            self.stderr.write(f"Error: {e}")
