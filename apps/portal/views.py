"""
Views for the product management portal.

This module handles the presentation layer for product management portal features.
Views delegate business logic to services.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages

from apps.common.mixins import AttachmentMixin
from apps.portal.forms import PortalProductForm, PortalProductRoleAssignmentForm, ProductSettingsForm, AgreementTemplateForm
from .services import (
    PortalService,
    BountyService,
    ProductUserService,
    ChallengeService,
    BountyDeliveryReviewService,
    PortalError,
    AgreementTemplateService,
)


class PortalBaseView(LoginRequiredMixin, TemplateView):
    """Base view for portal pages."""
    login_url = 'sign_in'
    portal_service = PortalService()
    
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
        return context


class PortalProductDetailView(PortalBaseView, AttachmentMixin):
    """View for product details, editing, and attachments."""
    template_name = "portal/products/detail.html"
    
    def get(self, request, slug):
        try:
            context = self.get_context_data()
            context.update(self.portal_service.get_product_detail_context(
                slug=slug,
                person=request.user.person
            ))
            if 'edit' in request.GET:
                context['form'] = PortalProductForm(instance=context['product'])
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def post(self, request, slug):
        try:
            if 'attachment' in request.FILES:
                return self.handle_attachment_upload(
                    request,
                    product_slug=slug,
                    redirect_url=reverse('portal:product-detail', args=[slug])
                )
                
            # Handle normal form submission
            product = self.portal_service.get_product_or_404(slug)
            form = PortalProductForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                messages.success(request, "Product updated successfully")
                return redirect('portal:product-detail', slug=slug)
            
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalProductListView(PortalBaseView):
    """List view for all products."""
    template_name = "portal/products/list.html"
    
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
    template_name = "portal/products/settings.html"
    
    def get(self, request, slug):
        try:
            context = self.portal_service.get_product_settings_context(
                slug=slug,
                person=request.user.person
            )
            context['form'] = ProductSettingsForm(instance=context['product'])
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def post(self, request, slug):
        try:
            product = self.portal_service.get_product_or_404(slug)
            form = ProductSettingsForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                messages.success(request, "Product settings updated successfully.")
                return redirect('portal:product-detail', slug=slug)
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalBountyListView(PortalBaseView):
    """List view for product bounties."""
    template_name = "portal/bounties/list.html"
    
    def get(self, request, slug):
        try:
            context = self.portal_service.get_product_bounties_context(
                slug=slug,
                person=request.user.person
            )
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalBountyClaimView(PortalBaseView):
    """View for managing bounty claims."""
    template_name = "portal/bounties/claims.html"
    
    def get(self, request, slug, pk):
        try:
            context = self.portal_service.get_bounty_claims_context(
                slug=slug,
                bounty_id=pk,
                person=request.user.person
            )
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalMyBountiesView(PortalBaseView):
    """View for user's claimed bounties."""
    template_name = "portal/bounties/my_bounties.html"
    
    def get(self, request, slug):
        try:
            context = self.portal_service.get_my_bounties_context(
                slug=slug,
                person=request.user.person
            )
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalChallengeListView(PortalBaseView):
    """View for managing challenges."""
    template_name = "portal/challenges/manage.html"
    challenge_service = ChallengeService()
    
    def get(self, request, slug):
        try:
            context = self.get_context_data()
            context.update(self.challenge_service.get_challenges_context(
                slug=slug,
                person=request.user.person
            ))
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class BountyClaimActionView(PortalBaseView):
    """Handle bounty claim actions."""
    portal_service = PortalService()
    
    def post(self, request, slug, pk, claim_id):
        try:
            action = request.POST.get('action')
            if action not in ['accept', 'reject']:
                messages.error(request, "Invalid action")
                return redirect('portal:bounty-claims', slug=slug, pk=pk)
                
            self.portal_service.handle_bounty_claim_action(
                slug=slug,
                bounty_id=pk,
                claim_id=claim_id,
                action=action,
                person=request.user.person
            )
            
            messages.success(request, f"Bounty claim {action}ed successfully")
            return redirect('portal:bounty-claims', slug=slug, pk=pk)
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
    template_name = "portal/products/users/manage.html"
    product_user_service = ProductUserService()

    def get(self, request, product_slug):
        context = super().get_context_data()
        context.update(
            self.product_user_service.get_product_users_context(product_slug)
        )
        return render(request, self.template_name, context)


class PortalAddProductUserView(PortalBaseView):
    """View for adding users to a product."""
    template_name = "portal/products/users/add.html"
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
    template_name = "portal/products/users/update.html"
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
    template_name = "portal/work/review.html"
    review_service = BountyDeliveryReviewService()
    
    def get(self, request, slug):
        try:
            context = self.get_context_data()
            context.update(self.review_service.get_review_context(
                slug=slug,
                person=request.user.person
            ))
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
            
    def post(self, request, slug):
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
            return redirect('portal:work-review', slug=slug)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalAgreementTemplatesView(PortalBaseView):
    """View for managing agreement templates."""
    template_name = "portal/agreements/templates.html"
    agreement_service = AgreementTemplateService()
    
    def get(self, request, slug):
        try:
            context = self.get_context_data()
            context.update(self.agreement_service.get_templates_context(
                slug=slug,
                person=request.user.person
            ))
            context['form'] = AgreementTemplateForm()
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def post(self, request, slug):
        try:
            form = AgreementTemplateForm(request.POST)
            if form.is_valid():
                if request.POST.get('template_id'):
                    # Update existing template
                    self.agreement_service.update_template(
                        slug=slug,
                        template_id=request.POST['template_id'],
                        person=request.user.person,
                        data=form.cleaned_data
                    )
                    messages.success(request, "Agreement template updated successfully")
                else:
                    # Create new template
                    self.agreement_service.create_template(
                        slug=slug,
                        person=request.user.person,
                        data=form.cleaned_data
                    )
                    messages.success(request, "Agreement template created successfully")
                return redirect('portal:agreement-templates', slug=slug)
            
            # If form is invalid, show errors
            context = self.get_context_data()
            context.update(self.agreement_service.get_templates_context(
                slug=slug,
                person=request.user.person
            ))
            context['form'] = form
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def delete(self, request, slug):
        try:
            template_id = request.POST.get('template_id')
            if not template_id:
                raise PortalError("Template ID is required")
                
            self.agreement_service.delete_template(
                slug=slug,
                template_id=template_id,
                person=request.user.person
            )
            messages.success(request, "Agreement template deleted successfully")
            return redirect('portal:agreement-templates', slug=slug)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalDashboardView(PortalBaseView):
    """Dashboard view for portal."""
    template_name = "portal/dashboard.html"
    
    def get(self, request):
        try:
            context = self.portal_service.get_dashboard_context(
                person=request.user.person
            )
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)