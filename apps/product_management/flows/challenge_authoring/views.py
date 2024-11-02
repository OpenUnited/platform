"""
Views for the challenge authoring flow.

This module handles the presentation layer of the challenge creation process,
implementing a multi-step form flow with AJAX support and real-time validation.

Flow Steps:
1. GET /<product_slug>/challenge/create/
   - Renders initial form with product context
   
2. POST /<product_slug>/challenge/create/
   - Handles form submission
   - Validates data
   - Creates challenge and bounties
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, FormView
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from apps.security.services import RoleService

from .forms import ChallengeAuthoringForm, BountyAuthoringForm
from .services import ChallengeAuthoringService

class ChallengeAuthoringView(LoginRequiredMixin, FormView):
    """Main view for the challenge authoring process."""
    
    template_name = "main.html"
    form_class = ChallengeAuthoringForm

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'person'):
            raise PermissionDenied("User profile not found")
            
        self.product = ChallengeAuthoringService.Product.objects.get_object_or_404(slug=kwargs['product_slug'])
        
        if not RoleService.is_product_manager(
            person=request.user.person,
            product=self.product
        ):
            raise PermissionDenied("You don't have permission to create challenges")
            
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = ChallengeAuthoringService(self.request.user, self.kwargs['product_slug'])
        context['skills'] = service.get_skills_list()
        return context

    def post(self, request, *args, **kwargs):
        challenge_form = ChallengeAuthoringForm(request.POST, product=self.get_product())
        bounty_forms = self._get_bounty_forms(request.POST)
        
        if challenge_form.is_valid() and all(form.is_valid() for form in bounty_forms):
            service = ChallengeAuthoringService(request.user, kwargs['product_slug'])
            
            if errors := service.validate_data(
                challenge_form.cleaned_data,
                [form.cleaned_data for form in bounty_forms]
            ):
                return JsonResponse({"status": "error", "errors": errors})
                
            success, challenge, errors = service.create_challenge(
                challenge_form.cleaned_data,
                [form.cleaned_data for form in bounty_forms]
            )
            
            if success:
                return JsonResponse({
                    "status": "success",
                    "challenge_id": challenge.id,
                    "redirect_url": reverse('challenge_detail', kwargs={
                        'product_slug': kwargs['product_slug'],
                        'pk': challenge.id
                    })
                })
            return JsonResponse({"status": "error", "errors": errors})
            
        return JsonResponse({
            "status": "error",
            "errors": self._get_form_errors(challenge_form, bounty_forms)
        })

    def _get_bounty_forms(self, data):
        total_forms = int(data.get('bounty-TOTAL_FORMS', 0))
        return [
            BountyAuthoringForm(
                data,
                prefix=f'bounty-{i}'
            ) for i in range(total_forms)
        ]

    def _get_form_errors(self, challenge_form, bounty_forms):
        errors = challenge_form.errors
        for i, form in enumerate(bounty_forms):
            if form.errors:
                errors[f'bounty_{i}'] = form.errors
        return errors

class SkillsListView(LoginRequiredMixin, View):
    def get(self, request):
        service = ChallengeAuthoringService(request.user)
        skills = service.get_skills_list()
        return JsonResponse({'skills': skills})

class SkillExpertiseView(LoginRequiredMixin, View):
    def get(self, request, skill_id):
        service = ChallengeAuthoringService(request.user)
        expertise = service.get_expertise_for_skill(skill_id)
        return JsonResponse({'expertise': expertise})
