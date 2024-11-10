from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from apps.capabilities.security.services import RoleService
from ..models import Product, Bounty, Challenge

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
            
            # If product is GLOBAL, allow access without authentication
            if product.visibility == Product.Visibility.GLOBAL:
                print("Product is GLOBAL, allowing access")  # Debug print
                return super().dispatch(request, *args, **kwargs)
            
            print("Product is not GLOBAL, checking authentication")  # Debug print
            
            # At this point, product is not GLOBAL, so we need authentication
            if not request.user.is_authenticated:
                print("User not authenticated, redirecting to login")  # Debug print
                return redirect_to_login(request.get_full_path())
            
            # Check if authenticated user has access
            if not RoleService.can_access_product_by_visibility(request.user.person, product):
                print("User does not have access, raising PermissionDenied")  # Debug print
                raise PermissionDenied
            
            print("All checks passed, proceeding with dispatch")  # Debug print
            return super().dispatch(request, *args, **kwargs)
            
        except Exception as e:
            print(f"Exception occurred: {str(e)}")  # Debug print
            raise