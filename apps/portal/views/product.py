"""Product-related views for the portal application."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic.edit import CreateView
from django.urls import reverse, reverse_lazy
from apps.capabilities.product_management.models import Product
from apps.common.exceptions import InvalidInputError
from apps.common.mixins import AttachmentMixin
from apps.portal.forms import (
    PortalProductForm,
    PortalProductRoleAssignmentForm,
    ProductSettingsForm,
    CreateProductForm,
)
from apps.capabilities.product_management.services import ProductManagementService
from apps.portal.services.portal_services import PortalError, ProductUserService
from .base import PortalBaseView
import logging

logger = logging.getLogger(__name__)

class PortalProductSummaryView(PortalBaseView, AttachmentMixin):
    """View for product dashboard/overview page."""
    template_name = "portal/product/summary.html"
    
    def get(self, request, product_slug):
        try:
            context = self.get_context_data()
            context.update(self.portal_service.get_product_detail_context(
                slug=product_slug,
                person=request.user.person
            ))
            if 'edit' in request.GET:
                context['form'] = PortalProductForm(instance=context['product'])
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def post(self, request, product_slug):
        try:
            if 'attachment' in request.FILES:
                return self.handle_attachment_upload(
                    request,
                    product_slug=product_slug,
                    redirect_url=reverse('portal:product-summary', args=[product_slug])
                )
                
            product = self.portal_service.get_product_or_404(product_slug)
            form = PortalProductForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                messages.success(request, "Product updated successfully")
                return redirect('portal:product-summary', product_slug=product_slug)
            
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)

class PortalProductListView(PortalBaseView):
    """List view for all products."""
    template_name = "portal/product/list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context.update(self.portal_service.get_products_context(
                person=self.request.user.person
            ))
            return context
        except PortalError as e:
            messages.warning(self.request, str(e))
            return context

class PortalProductSettingsView(PortalBaseView):
    """Settings view for a product."""
    template_name = "portal/product/settings/general.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_slug = self.kwargs.get('product_slug')
        product = get_object_or_404(Product, slug=product_slug)
        
        if not self.role_service.has_product_management_access(self.request.user.person, product):
            messages.error(self.request, "You do not have management access to this product")
            return redirect('portal:dashboard')

        if 'form' not in context:
            context['form'] = ProductSettingsForm(instance=product)
            
        context.update({
            'product': product,
            'product_slug': product_slug,
            'last_segment': 'settings',
            'can_modify_product': True
        })
        return context

    def get(self, request, product_slug):
        try:
            context = self.get_context_data()
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)

    def post(self, request, product_slug):
        try:
            product = get_object_or_404(Product, slug=product_slug)
            
            if not self.role_service.has_product_management_access(request.user.person, product):
                messages.error(request, "You do not have management access to this product")
                return redirect('portal:dashboard')
            
            form = ProductSettingsForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                messages.success(request, "Product settings updated successfully")
                return redirect('portal:product-settings', product_slug=product_slug)
            
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)

class PortalManageUsersView(PortalBaseView):
    """View for managing product users."""
    template_name = "portal/product/users/manage.html"
    product_user_service = ProductUserService()

    def get(self, request, product_slug):
        context = super().get_context_data()
        context.update(
            self.product_user_service.get_product_users_context(product_slug)
        )
        return render(request, self.template_name, context)

class PortalAddProductUserView(PortalBaseView):
    """View for adding users to a product."""
    template_name = "portal/product/users/add.html"
    product_user_service = ProductUserService()

    def get(self, request, product_slug):
        context = super().get_context_data()
        context['form'] = PortalProductRoleAssignmentForm()
        return render(request, self.template_name, context)

    def post(self, request, product_slug):
        form = PortalProductRoleAssignmentForm(request.POST)
        if form.is_valid():
            try:
                self.product_user_service.assign_user_role(
                    product_slug=product_slug,
                    person=form.cleaned_data['person'],
                    role=form.cleaned_data['role']
                )
                messages.success(request, "User successfully added to product.")
                return redirect('portal:manage-users', product_slug=product_slug)
            except ValueError as e:
                messages.error(request, str(e))
        
        context = super().get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)

class PortalUpdateProductUserView(PortalBaseView):
    """View for updating product user roles."""
    template_name = "portal/product/users/update.html"
    product_user_service = ProductUserService()

    def get(self, request, product_slug, user_id):
        context = super().get_context_data()
        context['form'] = PortalProductRoleAssignmentForm(
            instance=self.product_user_service.get_user_role_assignment(
                product_slug=product_slug,
                user_id=user_id
            )
        )
        return render(request, self.template_name, context)

    def post(self, request, product_slug, user_id):
        form = PortalProductRoleAssignmentForm(request.POST)
        if form.is_valid():
            try:
                self.product_user_service.update_user_role(
                    product_slug=product_slug,
                    user_id=user_id,
                    role=form.cleaned_data['role']
                )
                messages.success(request, "User role successfully updated.")
                return redirect('portal:manage-users', product_slug=product_slug)
            except ValueError as e:
                messages.error(request, str(e))

class CreateProductView(PortalBaseView):
    """View for creating new products."""
    template_name = 'portal/product/create.html'
    
    def get(self, request, org_id):
        context = self.get_context_data()
        logger.info(f"CreateProductView GET - org_id: {org_id}, current_org: {self.current_organisation}")
        
        if not self.current_organisation:
            messages.error(request, "Please select or create an organisation first")
            return redirect('portal:dashboard')
            
        form = CreateProductForm(organisation=self.current_organisation)
        context.update({
            'form': form,
            'organisation': self.current_organisation
        })
        return render(request, self.template_name, context)
    
    def post(self, request, org_id):
        logger.info(f"CreateProductView POST - org_id: {org_id}")
        logger.info(f"Current organisation: {self.current_organisation}")
        
        form = CreateProductForm(
            request.POST, 
            request.FILES,
            organisation=self.current_organisation
        )
        
        if form.is_valid():
            logger.info(f"Form is valid, cleaned_data: {form.cleaned_data}")
            try:
                product = ProductManagementService.create_product(
                    form_data=form.cleaned_data,
                    person=request.user.person,
                    organisation=self.current_organisation
                )
                logger.info(f"Product created successfully: {product.id} - {product.name}")
                messages.success(request, "Product created successfully")
                return redirect('portal:product-summary', product_slug=product.slug)
            except InvalidInputError as e:
                logger.error(f"Error creating product: {str(e)}")
                messages.error(request, str(e))
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            
        context = self.get_context_data()
        context.update({
            'form': form,
            'organisation': self.current_organisation
        })
        return render(request, self.template_name, context)
