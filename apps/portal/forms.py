from django import forms
from django.core.exceptions import ValidationError
from apps.capabilities.product_management.models import Product, FileAttachment
from apps.capabilities.security.models import ProductRoleAssignment
from apps.capabilities.commerce.models import Organisation
from apps.capabilities.security.services import RoleService
from apps.capabilities.product_management.forms import ProductForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import View
from apps.capabilities.commerce.models import Organisation
from apps.capabilities.talent.models import Person
from apps.capabilities.product_management.models import ProductContributorAgreementTemplate

class PortalBaseForm(forms.ModelForm):
    """Base form with common styling and functionality."""
    
    # Common CSS classes
    INPUT_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
    SELECT_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
    TEXTAREA_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
    CHECKBOX_CLASSES = "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_common_styles()
    
    def apply_common_styles(self):
        """Apply consistent styling to form fields."""
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.URLInput, forms.EmailInput)):
                field.widget.attrs['class'] = self.INPUT_CLASSES
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = self.SELECT_CLASSES
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = self.TEXTAREA_CLASSES
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = self.CHECKBOX_CLASSES

class PortalProductForm(PortalBaseForm):
    """Form for creating/editing products."""
    
    class Meta:
        model = Product
        fields = [
            'name',
            'organisation',
            'short_description',
            'full_description',
            'website',
            'video_url',
            'detail_url',
            'photo',
            'visibility'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.capabilities.commerce.models import Organisation
        self.fields['organisation'].queryset = Organisation.objects.all()

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

class PortalProductSettingView(LoginRequiredMixin, View):
    template_name = "portal/templates/product_settings.html"

    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        form = ProductForm(instance=product)
        
        context = {
            'form': form,
            'product': product,
            'detail_url': product.get_absolute_url(),
        }
        return render(request, self.template_name, context)

class ProductSettingsForm(forms.ModelForm):
    owner_type = forms.ChoiceField(
        choices=[
            ('person', 'Individual'),
            ('organisation', 'Organisation')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'short_description',
            'full_description',
            'website',
            'video_url',
            'photo',
            'visibility',
            'person',
            'organisation'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product Name'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of your product'
            }),
            'full_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed description of your product'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/...'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-control'
            }, choices=Product.Visibility.choices),
            'person': forms.Select(attrs={
                'class': 'form-control'
            }),
            'organisation': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['visibility'].help_text = """
            Global: Visible to everyone
            Organisation Only: Visible only to organisation members
            Restricted: Visible only to specific users
        """
        
        # Set initial owner_type based on current ownership
        instance = kwargs.get('instance')
        if instance:
            self.fields['owner_type'].initial = instance.owner_type

        # Hide person/organisation fields initially - they'll be shown/hidden via JS
        self.fields['person'].widget = forms.HiddenInput()
        self.fields['organisation'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        owner_type = cleaned_data.get('owner_type')
        person = cleaned_data.get('person')
        organisation = cleaned_data.get('organisation')

        # Validate ownership based on owner_type
        if owner_type == 'person':
            if not person:
                raise ValidationError("Person owner must be selected")
            cleaned_data['organisation'] = None
        elif owner_type == 'organisation':
            if not organisation:
                raise ValidationError("Organisation owner must be selected")
            cleaned_data['person'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set ownership based on owner_type
        owner_type = self.cleaned_data.get('owner_type')
        if owner_type == 'person':
            instance.organisation = None
            instance.person = self.cleaned_data.get('person')
        else:
            instance.person = None
            instance.organisation = self.cleaned_data.get('organisation')

        if commit:
            instance.save()
        return instance

class AgreementTemplateForm(PortalBaseForm):
    """Form for creating/editing agreement templates."""
    
    class Meta:
        model = ProductContributorAgreementTemplate
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }
