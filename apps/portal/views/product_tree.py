"""Product tree-related views for the portal application."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from apps.capabilities.product_management.models import Product
from apps.capabilities.security.services import RoleService
from apps.portal.services.product_tree_services import ProductTreeService
from .base import PortalBaseView
from apps.portal.utils.json_utils import TreeJSONEncoder
import json
import logging

logger = logging.getLogger(__name__)

class ProductTreeView(PortalBaseView):
    """View for creating a new product tree."""
    template_name = 'portal/product/product_trees/edit.html'
    
    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        
        # Get your tree data
        tree_data = {
            "name": product.name,
            "description": product.full_description,
            "children": []  # Add your actual tree data here
        }
        
        context = self.get_context_data()
        context.update({
            'product': product,
            'current_organisation': product.organisation,
            'tree_data': json.dumps(tree_data),
            'can_edit': RoleService.has_product_management_access(request.user.person, product)
        })
        return render(request, self.template_name, context)


class CreateProductTreeView(PortalBaseView):
    """View for showing the initial tree creation form."""
    template_name = "portal/product/product_trees/create.html"
    
    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        if not RoleService.has_product_management_access(request.user.person, product):
            messages.error(request, "You don't have permission to create product trees")
            return redirect('portal:product-summary', product_slug=product_slug)
            
        context = self.get_context_data()
        context.update({
            'product': product,
            'page_title': f"Create Product Tree - {product.name}"
        })
        return render(request, self.template_name, context)


@method_decorator(csrf_protect, name='dispatch')
class GenerateProductTreeView(PortalBaseView):
    """API endpoint for generating product tree."""
    template_name = 'portal/product/product_trees/edit.html'
    
    def post(self, request, product_slug):
        try:
            product = get_object_or_404(Product, slug=product_slug)
            
            if not RoleService.has_product_management_access(request.user.person, product):
                messages.error(request, "You don't have permission to edit this product")
                return redirect('portal:view-product-tree', product_slug=product_slug)
            
            additional_context = request.POST.get('context', '')
            
            tree_service = ProductTreeService()
            try:
                success, tree_data, error = tree_service.generate_initial_tree(
                    product=product,
                    additional_context=additional_context
                )
                
                logger.info(f"View received tree_data type: {type(tree_data)}")
                logger.debug("Tree data received from service", extra={'tree_data': tree_data})
                
                if success:
                    logger.info("Initial tree structure", extra={
                        'tree': json.dumps(tree_data, indent=2)
                    })
                    
                    # Deep copy with verification
                    import copy
                    tree_data_copy = copy.deepcopy(tree_data)
                    logger.info("Tree after deep copy", extra={
                        'tree': json.dumps(tree_data_copy, indent=2)
                    })
                    
                    def prepare_node_for_template(node, path="root"):
                        """Prepare node while preserving all children"""
                        if not isinstance(node, dict):
                            logger.error(f"Invalid node type at {path}: {type(node)}")
                            return None
                        
                        # Create new node with all fields
                        prepared_node = {
                            'name': str(node.get('name', '')),
                            'description': str(node.get('description', '')),
                            'lens_type': str(node.get('lens_type', 'experience')),
                            'children': []  # Initialize empty children list
                        }
                        
                        # Process children if they exist
                        if 'children' in node and isinstance(node['children'], list):
                            for i, child in enumerate(node['children']):
                                if isinstance(child, dict):
                                    prepared_child = prepare_node_for_template(child, f"{path}.children[{i}]")
                                    if prepared_child:
                                        prepared_node['children'].append(prepared_child)
                        
                            logger.info(f"Processed children at {path}", extra={
                                'children_count': len(prepared_node['children']),
                                'children': json.dumps(prepared_node['children'], indent=2)
                            })
                        
                        logger.info(f"Prepared node at {path}", extra={
                            'node': json.dumps(prepared_node, indent=2)
                        })
                        return prepared_node
                    
                    # Prepare the tree
                    serializable_tree = prepare_node_for_template(tree_data_copy)
                    logger.info("Final tree before serialization", extra={
                        'tree': json.dumps(serializable_tree, indent=2)
                    })
                    
                    # Convert to JSON string
                    json_tree = json.dumps(serializable_tree, cls=TreeJSONEncoder)
                    logger.debug("JSON string", extra={
                        'json': json_tree
                    })
                    
                    # Parse back to verify structure
                    parsed_tree = json.loads(json_tree)
                    logger.debug("Post-parse verification", extra={
                        'parsed': repr(parsed_tree)
                    })
                    
                    context = self.get_context_data()
                    context.update({
                        'product': product,
                        'tree_data': json_tree,
                        'current_organisation': product.organisation,
                        'edit_mode': True
                    })
                    return render(request, self.template_name, context)
                
                messages.error(request, f"Failed to generate tree: {error}")
                return redirect('portal:create-product-tree', product_slug=product_slug)
            
            except Exception as e:
                logger.exception("Error in tree generation", extra={'error': str(e)})
                if '503' in str(e):
                    messages.error(request, "The AI service is temporarily unavailable.")
                else:
                    messages.error(request, "Failed to generate tree.")
                return redirect('portal:create-product-tree', product_slug=product_slug)

        except Exception as e:
            logger.exception("Unexpected error in GenerateProductTreeView")
            messages.error(request, "An unexpected error occurred.")
            return redirect('portal:create-product-tree', product_slug=product_slug)


@method_decorator(csrf_protect, name='dispatch')
class RefineProductTreeView(PortalBaseView):
    """View for refining product tree."""
    template_name = 'portal/product/product_trees/edit.html'
    
    def post(self, request, product_slug):
        try:
            product = get_object_or_404(Product, slug=product_slug)
            logger.info(f"Starting tree refinement for product: {product.name}")
            
            if not RoleService.has_product_management_access(request.user.person, product):
                messages.error(request, "You don't have permission to edit this product")
                return redirect('portal:view-product-tree', product_slug=product_slug)
            
            try:
                current_tree = json.loads(request.POST.get('current_tree', '{}'))
                logger.debug("Current tree data:", extra={'tree': current_tree})
                
                feedback = request.POST.get('feedback')
                logger.info(f"Received feedback: {feedback}")
                
                tree_service = ProductTreeService()
                success, tree_data, error = tree_service.refine_tree(
                    product=product,
                    current_tree=current_tree,
                    feedback=feedback
                )
                
                logger.info(f"View received tree_data type: {type(tree_data)}")
                logger.debug("Tree data received from service", extra={'tree_data': tree_data})
                
                if success:
                    logger.info("Initial tree structure", extra={
                        'tree': json.dumps(tree_data, indent=2)
                    })
                    
                    # Deep copy with verification
                    import copy
                    tree_data_copy = copy.deepcopy(tree_data)
                    logger.info("Tree after deep copy", extra={
                        'tree': json.dumps(tree_data_copy, indent=2)
                    })
                    
                    def prepare_node_for_template(node, path="root"):
                        """Prepare node while preserving all children"""
                        if not isinstance(node, dict):
                            logger.error(f"Invalid node type at {path}: {type(node)}")
                            return None
                        
                        prepared_node = {
                            'name': str(node.get('name', '')),
                            'description': str(node.get('description', '')),
                            'lens_type': str(node.get('lens_type', 'experience')),
                            'children': []
                        }
                        
                        if 'children' in node and isinstance(node['children'], list):
                            for i, child in enumerate(node['children']):
                                if isinstance(child, dict):
                                    prepared_child = prepare_node_for_template(child, f"{path}.children[{i}]")
                                    if prepared_child:
                                        prepared_node['children'].append(prepared_child)
                            
                            logger.info(f"Processed children at {path}", extra={
                                'children_count': len(prepared_node['children']),
                                'children': json.dumps(prepared_node['children'], indent=2)
                            })
                        
                        logger.info(f"Prepared node at {path}", extra={
                            'node': json.dumps(prepared_node, indent=2)
                        })
                        return prepared_node
                    
                    # Prepare the tree
                    serializable_tree = prepare_node_for_template(tree_data_copy)
                    logger.info("Final tree before serialization", extra={
                        'tree': json.dumps(serializable_tree, indent=2)
                    })
                    
                    # Convert to JSON string
                    json_tree = json.dumps(serializable_tree, cls=TreeJSONEncoder)
                    logger.debug("JSON string", extra={'json': json_tree})
                    
                    # Parse back to verify structure
                    parsed_tree = json.loads(json_tree)
                    logger.debug("Post-parse verification", extra={
                        'parsed': repr(parsed_tree)
                    })
                    
                    context = self.get_context_data()
                    context.update({
                        'product': product,
                        'tree_data': json_tree,
                        'current_organisation': product.organisation,
                        'edit_mode': True
                    })
                    return render(request, self.template_name, context)
                
                messages.error(request, f"Failed to refine tree: {error}")
                return redirect('portal:view-product-tree', product_slug=product_slug)
                
            except Exception as e:
                logger.exception("Error in tree refinement", extra={'error': str(e)})
                if '503' in str(e):
                    messages.error(request, "The AI service is temporarily unavailable.")
                else:
                    messages.error(request, "Failed to refine tree.")
                return redirect('portal:view-product-tree', product_slug=product_slug)
                
        except Exception as e:
            logger.exception("Unexpected error in RefineProductTreeView")
            messages.error(request, "An unexpected error occurred.")
            return redirect('portal:view-product-tree', product_slug=product_slug)


@method_decorator(csrf_protect, name='dispatch')
class SaveProductTreeView(View):
    """View for saving final product tree."""
    
    def post(self, request, product_slug):
        try:
            product = get_object_or_404(Product, slug=product_slug)
            
            if not RoleService.has_product_management_access(request.user.person, product):
                messages.error(request, "You don't have permission to save this product tree")
                return redirect('portal:view-product-tree', product_slug=product_slug)
                
            tree = request.POST.get('tree')
            if not tree:
                messages.error(request, "No tree data provided")
                return redirect('portal:edit-product-tree', product_slug=product_slug)
            
            tree_service = ProductTreeService()
            success, error = tree_service.save_tree(
                product=product,
                tree=tree
            )
            
            if success:
                messages.success(request, "Product tree saved successfully")
                return redirect('portal:view-product-tree', product_slug=product_slug)
            else:
                messages.error(request, f"Failed to save tree: {error}")
                return redirect('portal:edit-product-tree', product_slug=product_slug)
                
        except Exception as e:
            logger.exception("Error in SaveProductTreeView")
            messages.error(request, f"An error occurred while saving the tree: {str(e)}")
            return redirect('portal:edit-product-tree', product_slug=product_slug)


class ViewProductTreeView(PortalBaseView):
    """View for displaying saved product tree."""
    template_name = "portal/product/product_trees/view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        tree_service = ProductTreeService()
        
        context.update({
            'product': product,
            'tree_data': tree_service.get_tree(product),
            'can_edit': RoleService.has_product_management_access(self.request.user.person, product),
            'page_title': f"Product Tree - {product.name}"
        })
        return context


class EditProductTreeView(PortalBaseView):
    """View for editing product tree."""
    template_name = "portal/product/product_trees/edit.html"
    
    def get(self, request, product_slug):
        try:
            product = get_object_or_404(Product, slug=product_slug)
            
            if not RoleService.has_product_management_access(request.user.person, product):
                messages.error(request, "Permission denied")
                return redirect('portal:view-product-tree', product_slug=product_slug)
            
            context = self.get_context_data()
            tree_service = ProductTreeService()
            tree_data = tree_service.get_tree(product)
            
            if tree_data is None:
                tree_data = {
                    "name": product.name,
                    "description": product.description or "",
                    "lens_type": "experience",
                    "children": []
                }
            
            context.update({
                'product': product,
                'tree_data': json.dumps(tree_data),  # Convert dict to JSON for template
                'edit_mode': True,
                'page_title': f"Edit Product Tree - {product.name}"
            })
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.exception("Error in EditProductTreeView")
            messages.error(request, "An error occurred")
            return redirect('portal:view-product-tree', product_slug=product_slug)
