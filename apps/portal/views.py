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
from apps.capabilities.security.services import RoleService
from django.conf import settings

from apps.common.mixins import AttachmentMixin
from apps.portal.forms import (
    PortalProductForm, 
    PortalProductRoleAssignmentForm, 
    ProductSettingsForm, 
    AgreementTemplateForm,
    OrganisationSettingsForm,
    CreateOrganisationForm,
    CreateProductForm,
    ProductForm,
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
from apps.capabilities.product_management.services import ProductManagementService
from django.db import transaction

logger = logging.getLogger(__name__)


class PortalBaseView(LoginRequiredMixin, TemplateView):
    """Base view for portal pages."""
    def get_login_url(self):
        return reverse('security:sign_in')
    
    portal_service = PortalService()
    role_service = RoleService()
    
    def get_current_organisation(self, request):
        """Get the current organisation from session or default to first available."""
        # Add safety check for anonymous users
        if not request.user.is_authenticated:
            return None
            
        current_org_id = request.session.get('current_organisation_id')
        person = request.user.person
        
        # Get user's organizations
        roles_summary = self.role_service.get_person_roles_summary(person)
        user_orgs = [item['organisation'] for item in roles_summary['organisations']]
        
        if user_orgs:
            if current_org_id:
                # Try to find the org from session
                current_org = next((org for org in user_orgs if org.id == current_org_id), None)
                if current_org:
                    return current_org
            # If no org in session or not found, default to first
            return user_orgs[0]
        return None
    
    def dispatch(self, request, *args, **kwargs):
        """Common permission checking and org context setting."""
        # Add safety check for anonymous users
        if not request.user.is_authenticated:
            return redirect(self.get_login_url())
            
        try:
            # Set current_organisation as an instance variable
            self.current_organisation = self.get_current_organisation(request)
            return super().dispatch(request, *args, **kwargs)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def get_context_data(self, **kwargs):
        """Add common context data."""
        context = super().get_context_data(**kwargs)
        try:
            person = self.request.user.person
            
            # Get current organisation from session
            current_org_id = self.request.session.get('current_organisation_id')
            logger.info(f"Current org ID from session: {current_org_id}")
            
            # Get all user organizations
            user_orgs = RoleService.get_user_organisations(person)
            
            # Get current org
            current_org = None
            if current_org_id:
                current_org = Organisation.objects.filter(id=current_org_id).first()
            if not current_org and user_orgs.exists():
                current_org = user_orgs.first()
                
            # Get current product slug from URL if available
            current_product_slug = None
            if 'product_slug' in self.kwargs:
                current_product_slug = self.kwargs['product_slug']
                
            logger.info(f"Current product slug: {current_product_slug}")
                
            # Get products specifically for the current organization
            organisation_products = []
            if current_org:
                organisation_products = RoleService.get_organisation_products(current_org)
                logger.info(f"Found {len(organisation_products)} products for org {current_org.name}")
            
            context.update({
                'current_organisation': current_org,
                'user_organisations': user_orgs,
                'organisation_products': organisation_products,
                'current_product_slug': current_product_slug,
                'can_manage_org': current_org and RoleService.is_organisation_manager(
                    person, 
                    current_org
                ) if current_org else False
            })
            
        except Exception as e:
            logger.error(f"Error in PortalBaseView.get_context_data: {str(e)}")
            messages.error(self.request, "Error loading portal context")
        return context
    
    def handle_service_error(self, error: PortalError):
        """Handle service layer errors consistently."""
        messages.error(self.request, str(error))
        return redirect('portal:dashboard')


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
            user_orgs = RoleService.get_user_organisations(request.user.person)
            if not user_orgs.filter(id=org_id).exists():
                messages.error(request, "Access denied to this organisation")
                return redirect('portal:dashboard')
            # Set the current organisation ID in session when viewing org pages
            request.session['current_organisation_id'] = org_id
            request.session.modified = True
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add current_organisation_id to context for menu highlighting
        if 'org_id' in self.kwargs:
            context['current_organisation_id'] = int(self.kwargs['org_id'])
        return context


class OrganisationListView(OrganisationBaseView):
    """View for listing user's organisations"""
    template_name = "portal/organisation/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_organisations'] = RoleService.get_person_organisations_with_roles(
            self.request.user.person
        )
        context['page_title'] = "My Organisations"
        return context


class OrganisationDetailView(OrganisationBaseView):
    """View for organisation details and overview"""
    template_name = "portal/organisation/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = get_object_or_404(Organisation, id=self.kwargs['org_id'])
        
        # Update to use RoleService
        user_orgs = RoleService.get_user_organisations(self.request.user.person)
        
        context.update({
            'organisation': organisation,
            'products': RoleService.get_organisation_products(organisation),
            'can_manage': RoleService.is_organisation_manager(
                self.request.user.person,
                organisation
            )
        })
        return context


class SwitchOrganisationView(OrganisationBaseView):
    """Handle switching between organisations"""
    
    def post(self, request, org_id):
        logger.info(f"Attempting to switch to organisation {org_id}")
        person = request.user.person
        organisation = get_object_or_404(Organisation, id=org_id)
        
        logger.info(f"Found organisation: {organisation.name}")
        
        # Debug current roles
        roles = RoleService.get_organisation_roles(person, organisation)
        logger.info(f"User roles for org: {[r.role for r in roles]}")
        
        # Verify user has access to this organisation using RoleService
        has_access = RoleService.has_organisation_role(
            person, 
            organisation,
            [
                OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER,
                OrganisationPersonRoleAssignment.OrganisationRoles.MEMBER
            ]
        )
        logger.info(f"User has access: {has_access}")
        
        if not has_access:
            logger.warning(f"Access denied for user {person.id} to org {org_id}")
            messages.error(request, "Access denied to this organisation")
            return redirect('portal:organisations')
            
        # Debug session before
        logger.info(f"Session before switch: {dict(request.session)}")
        
        # Update the session with the new organisation
        request.session['current_organisation_id'] = organisation.id
        request.session.modified = True
        
        # Debug session after
        logger.info(f"Session after switch: {dict(request.session)}")
        
        messages.success(request, f"Switched to {organisation.name}")
        return redirect('portal:dashboard')


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
        
        # Check for admin rights (OWNER or MANAGER)
        if not RoleService.has_organisation_admin_rights(person, organisation):
            raise PermissionDenied("You must be an owner or manager to view organization members")
        
        context.update({
            'organisation': organisation,
            'members': RoleService.get_organisation_members(organisation),
            'can_manage': True,  # They must be admin to get here
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


class CreateOrganisationView(PortalBaseView):
    """View for creating new organisations"""
    template_name = "portal/organisation/create.html"

    def get(self, request):
        context = self.get_context_data()
        context['form'] = CreateOrganisationForm()
        return render(request, self.template_name, context)

    def post(self, request):
        form = CreateOrganisationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    organisation = form.save()
                    
                    # Use RoleService to assign the owner role
                    RoleService.assign_organisation_role(
                        person=request.user.person,
                        organisation=organisation,
                        role=OrganisationPersonRoleAssignment.OrganisationRoles.OWNER
                    )
                    
                    # Switch to the newly created organisation
                    request.session['current_organisation_id'] = organisation.id
                    request.session.modified = True
                    
                    logger.info(f"Created organisation {organisation.name} with owner {request.user.person.id}")
                    messages.success(request, "Organisation created successfully")
                    return redirect('portal:organisation-detail', org_id=organisation.id)
            except Exception as e:
                logger.error(f"Failed to create organisation: {str(e)}")
                messages.error(request, "Failed to create organisation")
                
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class CreateProductView(PortalBaseView):
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
                # Pass both person and organisation
                product = ProductManagementService.create_product(
                    form_data=form.cleaned_data,
                    person=request.user.person,  # Add this
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