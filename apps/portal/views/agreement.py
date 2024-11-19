"""Agreement template-related views for the portal application."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.db import transaction
from apps.capabilities.product_management.models import (
    Product,
    ProductContributorAgreementTemplate
)
from apps.capabilities.security.services import RoleService
from apps.portal.forms import AgreementTemplateForm
from apps.portal.services.portal_services import (
    PortalService,
    AgreementTemplateService,
    PortalError
)
from .base import PortalBaseView
import logging

logger = logging.getLogger(__name__)

class PortalAgreementTemplatesView(PortalBaseView):
    """View for managing agreement templates."""
    template_name = "portal/product/agreements/list.html"
    agreement_service = AgreementTemplateService()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        
        if not RoleService.has_product_management_access(self.request.user.person, product):
            raise PermissionDenied("You don't have permission to view agreement templates")
            
        templates = ProductContributorAgreementTemplate.objects.filter(
            product=product
        ).order_by('-created_at')
        
        context.update({
            'product': product,
            'templates': templates,
            'can_create': True,
            'page_title': f"Agreement Templates - {product.name}",
            'active_tab': 'agreements'
        })
        return context

    def get(self, request, product_slug):
        try:
            context = self.get_context_data()
            return render(request, self.template_name, context)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('portal:product-summary', product_slug=product_slug)
        except Exception as e:
            logger.exception("Error in PortalAgreementTemplatesView")
            messages.error(request, "An error occurred while loading agreement templates")
            return redirect('portal:product-summary', product_slug=product_slug)


class CreateAgreementTemplateView(PortalBaseView):
    """View for creating new agreement templates."""
    template_name = "portal/product/agreements/create.html"
    agreement_service = AgreementTemplateService()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        
        if not RoleService.has_product_management_access(self.request.user.person, product):
            raise PermissionDenied("You don't have permission to create agreement templates")
            
        context.update({
            'product': product,
            'form': AgreementTemplateForm(),
            'page_title': f"Create Agreement Template - {product.name}",
            'active_tab': 'agreements'
        })
        return context

    def get(self, request, product_slug):
        try:
            context = self.get_context_data()
            return render(request, self.template_name, context)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('portal:agreement-templates', product_slug=product_slug)
        except Exception as e:
            logger.exception("Error in CreateAgreementTemplateView GET")
            messages.error(request, "An error occurred while loading the template form")
            return redirect('portal:agreement-templates', product_slug=product_slug)

    def post(self, request, product_slug):
        try:
            product = get_object_or_404(Product, slug=product_slug)
            
            if not RoleService.has_product_management_access(request.user.person, product):
                messages.error(request, "You don't have permission to create agreement templates")
                return redirect('portal:agreement-templates', product_slug=product_slug)
            
            form = AgreementTemplateForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        template = form.save(commit=False)
                        template.product = product
                        template.created_by = request.user.person
                        template.save()
                        
                        messages.success(request, "Agreement template created successfully")
                        return redirect('portal:agreement-templates', product_slug=product_slug)
                except Exception as e:
                    logger.exception("Error saving agreement template")
                    messages.error(request, "Failed to save agreement template")
            else:
                messages.error(request, "Please correct the errors below")
            
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.exception("Error in CreateAgreementTemplateView POST")
            messages.error(request, "An error occurred while creating the template")
            return redirect('portal:agreement-templates', product_slug=product_slug)


class ViewAgreementTemplateView(PortalBaseView):
    """View for displaying agreement template details."""
    template_name = "portal/product/agreements/view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        template = get_object_or_404(
            ProductContributorAgreementTemplate,
            id=self.kwargs['template_id'],
            product=product
        )
        
        if not RoleService.has_product_management_access(self.request.user.person, product):
            raise PermissionDenied("You don't have permission to view this template")
            
        context.update({
            'product': product,
            'template': template,
            'can_edit': True,
            'page_title': f"View Agreement Template - {template.name}",
            'active_tab': 'agreements'
        })
        return context

    def get(self, request, product_slug, template_id):
        try:
            context = self.get_context_data()
            return render(request, self.template_name, context)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('portal:agreement-templates', product_slug=product_slug)
        except Exception as e:
            logger.exception("Error in ViewAgreementTemplateView")
            messages.error(request, "An error occurred while loading the template")
            return redirect('portal:agreement-templates', product_slug=product_slug)


class EditAgreementTemplateView(PortalBaseView):
    """View for editing agreement templates."""
    template_name = "portal/product/agreements/edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        template = get_object_or_404(
            ProductContributorAgreementTemplate,
            id=self.kwargs['template_id'],
            product=product
        )
        
        if not RoleService.has_product_management_access(self.request.user.person, product):
            raise PermissionDenied("You don't have permission to edit this template")
            
        context.update({
            'product': product,
            'template': template,
            'form': AgreementTemplateForm(instance=template),
            'page_title': f"Edit Agreement Template - {template.name}",
            'active_tab': 'agreements'
        })
        return context

    def get(self, request, product_slug, template_id):
        try:
            context = self.get_context_data()
            return render(request, self.template_name, context)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('portal:view-agreement-template', 
                          product_slug=product_slug, 
                          template_id=template_id)
        except Exception as e:
            logger.exception("Error in EditAgreementTemplateView GET")
            messages.error(request, "An error occurred while loading the template")
            return redirect('portal:view-agreement-template', 
                          product_slug=product_slug, 
                          template_id=template_id)

    def post(self, request, product_slug, template_id):
        try:
            product = get_object_or_404(Product, slug=product_slug)
            template = get_object_or_404(
                ProductContributorAgreementTemplate,
                id=template_id,
                product=product
            )
            
            if not RoleService.has_product_management_access(request.user.person, product):
                messages.error(request, "You don't have permission to edit this template")
                return redirect('portal:view-agreement-template', 
                              product_slug=product_slug, 
                              template_id=template_id)
            
            form = AgreementTemplateForm(request.POST, instance=template)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        form.save()
                        messages.success(request, "Agreement template updated successfully")
                        return redirect('portal:view-agreement-template', 
                                     product_slug=product_slug, 
                                     template_id=template_id)
                except Exception as e:
                    logger.exception("Error saving agreement template")
                    messages.error(request, "Failed to save agreement template")
            else:
                messages.error(request, "Please correct the errors below")
            
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.exception("Error in EditAgreementTemplateView POST")
            messages.error(request, "An error occurred while updating the template")
            return redirect('portal:view-agreement-template', 
                          product_slug=product_slug, 
                          template_id=template_id)
