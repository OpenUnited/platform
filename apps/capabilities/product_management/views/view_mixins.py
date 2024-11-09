from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from apps.capabilities.security.services import RoleService

class ProductVisibilityCheckMixin:
    def get_product(self):
        obj = self.get_object()
        # If the object is already a Product, return it
        if hasattr(obj, 'visibility'):
            return obj
        # If the object has a product attribute (like Challenge), return that
        if hasattr(obj, 'product'):
            return obj.product
        raise AttributeError("Object must either be a Product or have a product attribute")

    def dispatch(self, request, *args, **kwargs):
        current_person = request.user.person if request.user.is_authenticated else None
        product = self.get_product()
        
        if not RoleService.can_access_product_by_visibility(current_person, product):
            raise PermissionDenied
            
        return super().dispatch(request, *args, **kwargs)