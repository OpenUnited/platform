"""
Views for the product management portal.

This module handles the presentation layer for product management portal features.
Views delegate business logic to services.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from apps.capabilities.product_management.models import Product
from apps.capabilities.commerce.models import Organisation
from apps.capabilities.security.models import OrganisationPersonRoleAssignment
from apps.capabilities.security.services import RoleService, OrganisationRoleService
from django.conf import settings

from apps.common.mixins import AttachmentMixin
from apps.portal.forms import (
    PortalProductForm, 
    PortalProductRoleAssignmentForm, 
    ProductSettingsForm, 
    AgreementTemplateForm,
    OrganisationSettingsForm,
)
from .services import (
    PortalService,
    BountyService,
    ProductUserService,
    ChallengeService,
    BountyDeliveryReviewService,
    PortalError,
    AgreementTemplateService,
)
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from apps.capabilities.product_management.models import Product  # Adjust import path as needed
from apps.capabilities.product_management.models import ProductContributorAgreementTemplate  # Adjust import path as needed
from django.core.exceptions import PermissionDenied
import logging
from django.db import connection
from django.db.models import Q

logger = logging.getLogger(__name__)


class PortalBaseView(LoginRequiredMixin, TemplateView):
    """Base view for portal pages."""
    login_url = 'sign_in'
    portal_service = PortalService()
    role_service = RoleService()
    
    def handle_service_error(self, error: PortalError):
        """Handle service layer errors consistently."""
        messages.error(self.request, str(error))
        return redirect('portal:dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        """Common permission checking."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def get_context_data(self, **kwargs):
        """Add common context data."""
        context = super().get_context_data(**kwargs)
        try:
            context.update(self.portal_service.get_user_context(self.request.user.person))
        except PortalError as e:
            messages.warning(self.request, str(e))
        # Add user's products to context for the sidebar using RoleService
        context['user_products'] = RoleService.get_user_products(self.request.user.person)
        
        # Add current product slug if it exists in the URL kwargs
        if 'product_slug' in self.kwargs:
            context['current_product_slug'] = self.kwargs['product_slug']
            
        # Get current org ID from session or URL
        current_org_id = self.request.session.get('current_organisation_id')
        if 'org_id' in self.kwargs:
            current_org_id = self.kwargs['org_id']
            
        # Get user's organizations and roles
        person = self.request.user.person
        roles_summary = self.role_service.get_person_roles_summary(person)
        user_orgs = [item['organisation'] for item in roles_summary['organisations']]
        
        # Get current org and its products
        current_org = None
        org_products = []
        if user_orgs:
            if current_org_id:
                current_org = next((org for org in user_orgs if org.id == current_org_id), user_orgs[0])
            else:
                current_org = user_orgs[0]
                
            if current_org:
                org_products = Product.objects.filter(organisation=current_org)
        
        context.update({
            'user_organisations': user_orgs,
            'current_organisation': current_org,
            'organisation_products': org_products,
            'can_manage_org': current_org and self.role_service.is_organisation_manager(
                person, 
                current_org
            ) if current_org else False
        })
        return context


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
                
            # Handle normal form submission
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
        
        # Check if user has management access
        if not RoleService.has_product_management_access(self.request.user.person, product):
            messages.error(self.request, "You do not have management access to this product")
            return redirect('portal:dashboard')

        # Add form if not already in context
        if 'form' not in context:
            context['form'] = ProductSettingsForm(instance=product)
            
        context.update({
            'product': product,
            'product_slug': product_slug,
            'last_segment': 'settings',
            'can_modify_product': True  # We already checked access above
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
            
            # Check if user has management access
            if not RoleService.has_product_management_access(request.user.person, product):
                messages.error(request, "You do not have management access to this product")
                return redirect('portal:dashboard')
            
            form = ProductSettingsForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                messages.success(request, "Product settings updated successfully")
                return redirect('portal:product-settings', product_slug=product_slug)
            
            # If form is invalid, add it to context and re-render
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalBountyListView(PortalBaseView):
    """List view for product bounties."""
    template_name = "portal/product/bounties/list.html"
    
    def get(self, request, product_slug):
        try:
            context = super().get_context_data(product_slug=product_slug)
            
            bounty_context = self.portal_service.get_product_bounties_context(
                slug=product_slug,
                person=request.user.person
            )
            context.update(bounty_context)
            
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalBountyClaimView(PortalBaseView):
    """View for managing bounty claims."""
    template_name = "portal/product/bounties/claims.html"
    
    def get(self, request, product_slug, pk):
        try:
            context = self.portal_service.get_bounty_claims_context(
                slug=product_slug,
                bounty_id=pk,
                person=request.user.person
            )
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalMyBountiesView(PortalBaseView):
    """View for user's claimed bounties."""
    template_name = "portal/product/bounties/my_bounties.html"
    
    def get(self, request, product_slug):
        try:
            context = self.portal_service.get_my_bounties_context(
                slug=product_slug,
                person=request.user.person
            )
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalChallengeListView(PortalBaseView):
    """View for managing challenges."""
    template_name = "portal/product/challenges/manage.html"
    challenge_service = ChallengeService()
    
    def get(self, request, product_slug):
        try:
            context = self.get_context_data()
            # Get base challenge context from service
            context.update(self.challenge_service.get_challenges_context(
                slug=product_slug,
                person=request.user.person
            ))
            
            # Handle search if present
            search_query = request.GET.get('search-challenge')
            if search_query:
                challenges = context['challenges'].filter(title__icontains=search_query)
                context['challenges'] = challenges
                context['search_query'] = search_query
                
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class BountyClaimActionView(PortalBaseView):
    """Handle bounty claim actions."""
    portal_service = PortalService()
    
    def post(self, request, product_slug, pk, claim_id):
        try:
            action = request.POST.get('action')
            if action not in ['accept', 'reject']:
                messages.error(request, "Invalid action")
                return redirect('portal:bounty-claims', product_slug=product_slug, pk=pk)
                
            self.portal_service.handle_bounty_claim_action(
                slug=product_slug,
                bounty_id=pk,
                claim_id=claim_id,
                action=action,
                person=request.user.person
            )
            
            messages.success(request, f"Bounty claim {action}ed successfully")
            return redirect('portal:bounty-claims', product_slug=product_slug, pk=pk)
        except PortalError as e:
            return self.handle_service_error(e)


class DeleteBountyClaimView(PortalBaseView):
    """View for cancelling bounty claims."""
    bounty_service = BountyService()

    def post(self, request, pk):
        try:
            self.bounty_service.handle_claim_action(pk, "cancel")
            messages.success(request, "The bounty claim was successfully cancelled.")
            return redirect('portal:bounty-requests')
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


class PortalWorkReviewView(PortalBaseView):
    """View for reviewing work."""
    template_name = "portal/product/work/review.html"
    review_service = BountyDeliveryReviewService()
    
    def get(self, request, product_slug):
        try:
            context = self.get_context_data()
            context.update(self.review_service.get_review_context(
                slug=product_slug,
                person=request.user.person
            ))
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
            
    def post(self, request, product_slug):
        try:
            attempt_id = request.POST.get('attempt_id')
            approved = request.POST.get('approved') == 'true'
            feedback = request.POST.get('feedback', '')
            
            self.review_service.review_delivery_attempt(
                attempt_id=attempt_id,
                approved=approved,
                feedback=feedback,
                reviewer=request.user.person
            )
            
            messages.success(request, "Work review submitted successfully")
            return redirect('portal:work-review', product_slug=product_slug)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalAgreementTemplatesView(PortalBaseView):
    """View for managing agreement templates."""
    template_name = "portal/product/agreements/templates.html"
    agreement_service = AgreementTemplateService()
    
    def get(self, request, product_slug):
        try:
            context = self.get_context_data()
            context.update(self.agreement_service.get_templates_context(
                slug=product_slug,
                person=request.user.person
            ))
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def post(self, request, product_slug):
        try:
            form = AgreementTemplateForm(request.POST)
            if form.is_valid():
                if request.POST.get('template_id'):
                    # Update existing template
                    self.agreement_service.update_template(
                        slug=product_slug,
                        template_id=request.POST['template_id'],
                        person=request.user.person,
                        data=form.cleaned_data
                    )
                    messages.success(request, "Agreement template updated successfully")
                else:
                    # Create new template
                    self.agreement_service.create_template(
                        slug=product_slug,
                        person=request.user.person,
                        data=form.cleaned_data
                    )
                    messages.success(request, "Agreement template created successfully")
                return redirect('portal:product-agreements', product_slug=product_slug)
            
            # If form is invalid, show errors
            context = self.get_context_data()
            context.update(self.agreement_service.get_templates_context(
                slug=product_slug,
                person=request.user.person
            ))
            context['form'] = form
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def delete(self, request, product_slug):
        try:
            template_id = request.POST.get('template_id')
            if not template_id:
                raise PortalError("Template ID is required")
                
            self.agreement_service.delete_template(
                slug=product_slug,
                template_id=template_id,
                person=request.user.person
            )
            messages.success(request, "Agreement template deleted successfully")
            return redirect('portal:agreement-templates', slug=product_slug)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalDashboardView(PortalBaseView):
    """Dashboard view for portal."""
    template_name = "portal/dashboard.html"
    
    def get(self, request):
        try:
            # Get base context which includes user_products
            context = self.get_context_data()
            # Add dashboard-specific context
            context.update(self.portal_service.get_dashboard_context(
                person=request.user.person
            ))
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalUserSettingsView(PortalBaseView):
    template_name = 'portal/user_settings.html'

    def get(self, request):
        return render(request, self.template_name, {
            'user': request.user
        })


class CreateAgreementTemplateView(PortalBaseView, LoginRequiredMixin):
    """View for creating agreement templates."""
    template_name = 'portal/product/agreements/create.html'
    
    def get(self, request, product_slug):
        context = self.get_context_data()
        context['form'] = AgreementTemplateForm()
        return render(request, self.template_name, context)
    
    def post(self, request, product_slug):
        try:
            form = AgreementTemplateForm(request.POST)
            if form.is_valid():
                AgreementTemplateService.create_template(
                    slug=product_slug,
                    person=request.user.person,
                    data=form.cleaned_data
                )
                messages.success(request, "Agreement template created successfully")
                return redirect('portal:product-agreements', product_slug=product_slug)
            
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
            
        except PortalError as e:
            return self.handle_service_error(e)


class OrganisationBaseView(PortalBaseView):
    """Base view for organisation-related views"""
    
    def dispatch(self, request, *args, **kwargs):
        if 'org_id' in kwargs:
            org_id = kwargs['org_id']
            user_orgs = OrganisationRoleService.get_user_organisations(request.user.person)
            if not user_orgs.filter(id=org_id).exists():
                messages.error(request, "Access denied to this organisation")
                return redirect('portal:dashboard')
        return super().dispatch(request, *args, **kwargs)


class OrganisationListView(OrganisationBaseView):
    """View for listing user's organisations"""
    template_name = "portal/organisation/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "My Organisations"
        return context


class OrganisationDetailView(OrganisationBaseView):
    """View for organisation details and overview"""
    template_name = "portal/organisation/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs['org_id']
        organisation = get_object_or_404(Organisation, id=org_id)
        person = self.request.user.person
        
        # Debug logging
        logger.info(f"Checking access for person {person.id} to org {organisation.id}")
        
        # Get the raw assignment record
        from apps.capabilities.security.models import OrganisationPersonRoleAssignment
        assignment = OrganisationPersonRoleAssignment.objects.filter(
            person=person,
            organisation=organisation
        ).first()
        
        if assignment:
            logger.info(f"Found role assignment: {assignment.role}")
            
            # Check specific role access using constants from model
            has_role = RoleService.has_organisation_role(
                person, 
                organisation,
                [
                    OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MEMBER
                ]
            )
            logger.info(f"Has required role: {has_role}")

            if not has_role:
                logger.warning(f"Access denied despite having role {assignment.role}")
                raise PermissionDenied("You don't have access to this organisation")
        else:
            logger.warning(f"No role assignment found for person {person.id} and org {organisation.id}")
            raise PermissionDenied("You don't have access to this organisation")
        
        # Get all organization members using the correct method
        members = RoleService.get_organisation_members(organisation)
        
        # Get the role assignments for display
        member_roles = OrganisationPersonRoleAssignment.objects.filter(
            organisation=organisation
        ).select_related('person')
        
        context.update({
            'organisation': organisation,
            'products': OrganisationRoleService.get_organisation_products(organisation),
            'members': member_roles,  # Contains the role information for the table
            'members_count': members.count(),  # Use the members queryset for the count
            'page_title': organisation.name,
            'can_manage': RoleService.is_organisation_manager(person, organisation)
        })
        return context


class SwitchOrganisationView(OrganisationBaseView):
    """Handle switching between organisations"""
    
    def post(self, request, org_id):
        person = request.user.person
        organisation = get_object_or_404(Organisation, id=org_id)
        
        # Verify user has access to this organisation
        if not RoleService.has_organisation_role(person, organisation, 
            ['OWNER', 'MANAGER', 'MEMBER']):
            messages.error(request, "Access denied to this organisation")
            return redirect('portal:dashboard')
            
        request.session['current_organisation_id'] = org_id
        messages.success(request, "Organisation context switched successfully")
        return redirect(request.META.get('HTTP_REFERER', 'portal:dashboard'))


class OrganisationSettingsView(OrganisationBaseView):
    """View for managing organisation settings"""
    template_name = "portal/organisation/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs['org_id']
        organisation = get_object_or_404(Organisation, id=org_id)
        person = self.request.user.person
        
        if not RoleService.is_organisation_manager(person, organisation):
            raise PermissionDenied("You don't have permission to manage this organisation")
            
        context.update({
            'organisation': organisation,
            'form': OrganisationSettingsForm(instance=organisation),
            'page_title': f"Settings - {organisation.name}"
        })
        return context

    def post(self, request, org_id):
        organisation = get_object_or_404(Organisation, id=org_id)
        person = request.user.person
        
        if not RoleService.is_organisation_manager(person, organisation):
            raise PermissionDenied("You don't have permission to manage this organisation")
            
        form = OrganisationSettingsForm(request.POST, request.FILES, instance=organisation)
        if form.is_valid():
            form.save()
            messages.success(request, "Organisation settings updated successfully")
            return redirect('portal:organisation-detail', org_id=org_id)
            
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class OrganisationMembersView(OrganisationBaseView):
    """View for managing organisation members"""
    template_name = "portal/organisation/members.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs['org_id']
        organisation = get_object_or_404(Organisation, id=org_id)
        person = self.request.user.person
        
        if not RoleService.has_organisation_role(person, organisation, 
            ['OWNER', 'MANAGER', 'MEMBER']):
            raise PermissionDenied("You don't have access to this organisation")
        
        context.update({
            'organisation': organisation,
            'members': RoleService.get_organisation_members(organisation),
            'can_manage': RoleService.is_organisation_manager(person, organisation),
            'page_title': f"Members - {organisation.name}"
        })
        return context


class ProductDetailView(PortalBaseView):
    template_name = "portal/product/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        person = self.request.user.person

        # Get product roles
        from apps.capabilities.security.models import ProductRoleAssignment
        product_roles = ProductRoleAssignment.objects.filter(
            product=product
        ).select_related('person')

        context.update({
            'product': product,
            'product_roles': product_roles,
        })
        return context


class ProductSummaryView(PortalBaseView):
    template_name = "portal/product/summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        
        # Get product roles
        from apps.capabilities.security.models import ProductRoleAssignment
        product_roles = ProductRoleAssignment.objects.filter(
            product=product
        ).select_related('person').order_by('person__full_name')

        context.update({
            'product': product,
            'product_roles': product_roles,
            'active_challenges_count': self.get_active_challenges_count(),
            'open_bounties_count': self.get_open_bounties_count(),
            'active_contributors_count': self.get_active_contributors_count(),
            'debug': settings.DEBUG,
        })
        return context