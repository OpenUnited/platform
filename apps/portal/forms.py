from django import forms
from django.core.exceptions import ValidationError
from apps.capabilities.product_management.models import Product
from apps.capabilities.security.models import ProductRoleAssignment
from apps.capabilities.commerce.models import Organisation
from apps.capabilities.security.services import RoleService
from apps.capabilities.product_management.forms import ProductForm
from apps.capabilities.security.models import Person

class PortalProductForm(ProductForm):
    """Portal-specific extension of ProductForm"""
    make_me_owner = forms.BooleanField(required=False)
    person = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        required=False,
        widget=forms.HiddenInput()
    )
    video_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'})
    )
    detail_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'sr-only'})
    )
    visibility = forms.ChoiceField(
        choices=Product.Visibility.choices,
        widget=forms.Select(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6'})
    )
    
    class Meta:
        model = Product
        fields = ['name', 'organisation', 'short_description', 'full_description', 'website', 'video_url', 'detail_url', 'photo', 'visibility', 'person']
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request and self.request.user.is_authenticated:
            managed_orgs = RoleService.get_managed_organisations(self.request.user.person)
            self.fields['organisation'].queryset = managed_orgs
        
        # Hide person field from form but keep it in fields
        self.fields['person'].widget = forms.HiddenInput()
        self.fields['person'].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        if cleaned_data.get('make_me_owner'):
            cleaned_data['person'] = self.request.user.person
            cleaned_data['organisation'] = None
        elif cleaned_data.get('organisation'):
            cleaned_data['person'] = None
        else:
            raise ValidationError("Please either make yourself the owner or select an organization")
        
        return cleaned_data

class PortalProductRoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = ProductRoleAssignment
        fields = ["person", "role"]
        widgets = {
            "role": forms.Select(
                attrs={
                    "class": (
                        "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                        " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    ),
                },
                choices=ProductRoleAssignment.ProductRoles.choices,
            ),
        }
