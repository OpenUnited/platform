from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from django.contrib import messages
from apps.capabilities.security.services import RoleService
from ..models import Product, Bounty, Challenge
from django.http import JsonResponse
from django.core.cache import cache
from functools import cached_property
import logging

logger = logging.getLogger(__name__)

class ProductVisibilityCheckMixin:
    def get_product(self):
        print("URL kwargs:", self.kwargs)  # Debug print
        
        # If we're looking at a bounty
        if 'bounty_id' in self.kwargs:
            print(f"Found bounty_id: {self.kwargs['bounty_id']}")  # Debug print
            bounty = get_object_or_404(Bounty, id=self.kwargs['bounty_id'])
            product = bounty.challenge.product
            print(f"Found product: {product.name}, visibility: {product.visibility}")  # Debug print
            return product
            
        # If we have a product slug directly
        if 'product_slug' in self.kwargs:
            print(f"Found product_slug: {self.kwargs['product_slug']}")  # Debug print
            product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
            print(f"Found product: {product.name}, visibility: {product.visibility}")  # Debug print
            return product
            
        raise ValueError("Cannot determine product from URL parameters")

    def dispatch(self, request, *args, **kwargs):
        print(f"\nStarting dispatch, authenticated: {request.user.is_authenticated}")  # Debug print
        
        try:
            # Get the product first, without requiring authentication
            product = self.get_product()
            print(f"Product visibility value: {product.visibility}")  # Debug print
            print(f"GLOBAL visibility value: {Product.Visibility.GLOBAL}")  # Debug print
            
            # Allow public access for global products
            if product.visibility == Product.Visibility.GLOBAL:
                print("Product is GLOBAL, allowing access")  # Debug print
                return super().dispatch(request, *args, **kwargs)
            
            print("Product is not GLOBAL, checking authentication")  # Debug print
            
            # For restricted products, check authentication
            if not request.user.is_authenticated:
                print("User not authenticated, redirecting to login")  # Debug print
                return redirect_to_login(request.get_full_path())
            
            try:
                # Ensure user has a person object
                if not hasattr(request.user, 'person'):
                    from apps.capabilities.talent.models import Person
                    person, _ = Person.objects.get_or_create(user=request.user)
                    request.user.person = person
                
                # Check product access
                if RoleService.has_product_access(request.user.person, product):
                    return super().dispatch(request, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error checking product access: {e}")
                raise
            
            raise PermissionDenied
            
        except Exception as e:
            print(f"Exception occurred: {str(e)}")  # Debug print
            raise

class ProductManagementRequiredMixin:
    """Mixin to enforce product management permissions"""
    
    def get_product(self):
        """Get product using same logic as ProductVisibilityCheckMixin"""
        if hasattr(self, 'object') and isinstance(self.object, Product):
            return self.object
            
        if 'bounty_id' in self.kwargs:
            bounty = get_object_or_404(Bounty, id=self.kwargs['bounty_id'])
            return bounty.challenge.product
            
        if 'product_slug' in self.kwargs:
            return get_object_or_404(Product, slug=self.kwargs['product_slug'])
            
        if 'pk' in self.kwargs:
            return get_object_or_404(Product, pk=self.kwargs['pk'])

        raise ValueError("Cannot determine product from URL parameters")

    def dispatch(self, request, *args, **kwargs):
        # Get the product first
        product = self.get_product()
        
        # Check if user has management access
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
            
        if not RoleService.has_product_management_access(request.user.person, product):
            raise PermissionDenied
            
        return super().dispatch(request, *args, **kwargs)

class ProductSuccessUrlMixin:
    """Mixin to handle product-related success URLs"""
    
    def get_success_url(self):
        if hasattr(self, 'success_url_name'):
            return reverse(f"product_management:{self.success_url_name}", 
                         kwargs={'product_slug': self.object.product.slug})
        return super().get_success_url()

class ProductServiceMixin:
    """Mixin to handle service layer interactions"""
    
    def handle_service_result(self, success, error_msg, redirect_url):
        if success:
            messages.success(self.request, "Operation completed successfully")
            return redirect(redirect_url)
        messages.error(self.request, error_msg)
        return self.form_invalid(self.get_form())

class ProductContextMixin:
    """Mixin to provide consistent context data"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # If this is a Challenge, get the photo URL from its product
        if hasattr(self.object, 'product'):
            photo_url = self.object.product.get_photo_url()
        else:
            # Otherwise assume it's a Product
            photo_url = self.object.get_photo_url()
        
        context.update({
            'can_manage': RoleService.has_product_management_access(
                self.request.user.person, 
                self.object
            ),
            'product': self.object,
            'product_photo_url': photo_url
        })
        return context

class ProductResponseMixin:
    """Standardize API responses and error handling"""
    
    def handle_error(self, error_msg, status=400):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(error_msg)}, status=status)
        messages.error(self.request, str(error_msg))
        return self.render_to_response(self.get_context_data(form=self.get_form()))
        
    def handle_success(self, redirect_url, message="Operation completed successfully"):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'redirect_url': redirect_url})
        messages.success(self.request, message)
        return redirect(redirect_url)

class ProductAccessMixin:
    """Mixin to handle cached product access checks"""
    
    @cached_property
    def can_manage_product(self):
        cache_key = f'product_manage_{self.object.id}_{self.request.user.id}'
        result = cache.get(cache_key)
        if result is None:
            result = RoleService.has_product_management_access(
                self.request.user.person, 
                self.object
            )
            cache.set(cache_key, result, 300)  # Cache for 5 minutes
        return result

    @cached_property
    def can_view_product(self):
        cache_key = f'product_view_{self.object.id}_{self.request.user.id}'
        result = cache.get(cache_key)
        if result is None:
            result = RoleService.can_access_product_by_visibility(
                self.request.user.person, 
                self.object
            )
            cache.set(cache_key, result, 300)
        return result