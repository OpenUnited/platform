"""Work-related views for the portal application."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from .base import PortalBaseView
from apps.portal.services.portal_services import (
    PortalService,
    BountyService,
    ChallengeService,
    BountyDeliveryReviewService,
    PortalError
)
import logging

logger = logging.getLogger(__name__)

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
            context.update(self.challenge_service.get_challenges_context(
                slug=product_slug,
                person=request.user.person
            ))
            
            search_query = request.GET.get('search-challenge')
            if search_query:
                challenges = context['challenges'].filter(title__icontains=search_query)
                context['challenges'] = challenges
                context['search_query'] = search_query
                
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)

@method_decorator(csrf_protect, name='dispatch')
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
