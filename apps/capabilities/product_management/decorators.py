from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import redirect_to_login

from apps.capabilities.security.services import RoleService
from .models import Product, Bounty, Challenge
from .services import ProductService

def get_product_from_kwargs(kwargs):
    """Helper function to get product from various URL kwargs patterns"""
    if 'product_slug' in kwargs:
        return get_object_or_404(Product, slug=kwargs['product_slug'])
        
    if 'bounty_id' in kwargs:
        bounty = get_object_or_404(Bounty, id=kwargs['bounty_id'])
        return bounty.challenge.product
        
    if 'challenge_id' in kwargs:
        challenge = get_object_or_404(Challenge, id=kwargs['challenge_id'])
        return challenge.product
        
    raise ValueError("Cannot determine product from URL parameters")

def require_product_management(view_func):
    """
    Decorator for function-based views requiring management permissions.
    
    Checks if the user:
    1. Is authenticated
    2. Has management access to the product
    
    Raises:
        PermissionDenied: If user doesn't have required permissions
        Http404: If product not found
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check authentication first
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
            
        try:
            product = get_product_from_kwargs(kwargs)
            if not RoleService.has_product_management_access(request.user.person, product):
                raise PermissionDenied("You don't have management access to this product")
            return view_func(request, *args, **kwargs)
        except ValueError as e:
            raise PermissionDenied(str(e))
            
    return wrapper

def require_product_visibility(view_func):
    """
    Decorator for function-based views requiring visibility access.
    
    Checks if:
    1. Product is public (GLOBAL visibility)
    2. Or user has required visibility access
    
    Raises:
        PermissionDenied: If user doesn't have required permissions
        Http404: If product not found
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            product = get_product_from_kwargs(kwargs)
            
            # Check if product is public
            if product.visibility == Product.Visibility.GLOBAL:
                return view_func(request, *args, **kwargs)
                
            # If not public, require authentication
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
                
            # Check visibility access
            if not RoleService.can_access_product_by_visibility(request.user.person, product):
                raise PermissionDenied("You don't have access to this product")
                
            return view_func(request, *args, **kwargs)
            
        except ValueError as e:
            raise PermissionDenied(str(e))
            
    return wrapper