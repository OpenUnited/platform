import uuid
from functools import wraps

from django.contrib import messages
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect

from apps.capabilities.security.models import ProductRoleAssignment
from apps.capabilities.security.services import RoleService

from .models import Product


def get_person_data(person):
    # Check if we received a User object instead of a Person
    if hasattr(person, 'person'):
        person = person.person
    elif hasattr(person, 'user'):
        # We already have a Person object
        pass
    else:
        return {"first_name": person.first_name, "username": person.username}

    return {
        "first_name": person.user.first_name,
        "username": person.user.username
    }


def to_dict(instance):
    result = model_to_dict(instance)
    return {key: (str(result[key]) if isinstance(result[key], uuid.UUID) else result[key]) for key in result.keys()}


def has_product_access(user, product):
    """Check if user has access to view the product"""
    if not user or not user.is_authenticated:
        return product.visibility == Product.Visibility.GLOBAL
    
    if not hasattr(user, 'person'):
        return False
        
    return True  # Add your actual access logic here


def permission_error_message():
    return "You don't have enough permission to perform this action."


def modify_permission_required(view_func):
    def _wrapped_view(self, request, *args, **kwargs):
        error_message = permission_error_message()
        if self.get_context_data().get("can_modify_product", False):
            return view_func(self, request, *args, **kwargs)
        else:
            if self.is_ajax():
                return JsonResponse({"error": error_message}, status=400)
            else:
                messages.success(self.request, error_message)
                return HttpResponseRedirect(self.get_success_url())

    return _wrapped_view


def serialize_tree(node):
    """Serializer for the tree."""
    return {
        "id": node.pk,
        "node_id": uuid.uuid4(),
        "name": node.name,
        "description": node.description,
        "video_link": node.video_link,
        "video_name": node.video_name,
        "video_duration": node.video_duration,
        "has_saved": True,
        "children": [serialize_tree(child) for child in node.get_children()],
    }


class BaseProductDetailView:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs.get("product_slug", None))
        context["product"] = product
        context["product_slug"] = product.slug
        return context


def require_product_management_access(view_func):
    @wraps(view_func)
    def wrapper(request, product_slug, *args, **kwargs):
        product = get_object_or_404(Product, slug=product_slug)
        if not RoleService.has_product_management_access(request.user.person, product):
            messages.error(request, "You do not have management access to this product")
            return redirect('portal:dashboard')
        return view_func(request, product_slug, *args, **kwargs)
    return wrapper
