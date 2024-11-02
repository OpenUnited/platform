"""
Views for the challenge authoring flow.

Flow Steps:
1. GET /<product_slug>/challenge/create/
   - Renders initial form with product context
   
2. POST /<product_slug>/challenge/create/
   - Handles form submission
   - Validates data
   - Creates challenge and bounties
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, FormView, CreateView
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from apps.security.services import RoleService
from django.conf import settings

from .forms import ChallengeAuthoringForm, BountyAuthoringForm
from .services import ChallengeAuthoringService
from apps.product_management.models import Product

class ChallengeAuthoringView(LoginRequiredMixin, CreateView):
    """Main view for challenge authoring flow."""
    form_class = ChallengeAuthoringForm
    template_name = 'main.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'person'):
            return redirect(settings.LOGIN_URL)
            
        self.product = get_object_or_404(Product, slug=kwargs['product_slug'])
        
        if not RoleService.is_product_manager(request.user.person, self.product):
            raise PermissionDenied("Must be product manager")
            
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('product_challenges', kwargs={'product_slug': self.kwargs['product_slug']})

    def form_valid(self, form):
        # Process the form data
        service = ChallengeAuthoringService(self.request.user, self.kwargs['product_slug'])
        service.create_challenge(form.cleaned_data)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context

class SkillsListView(LoginRequiredMixin, View):
    """View for retrieving skills list."""
    
    def get(self, request, product_slug):
        service = ChallengeAuthoringService(request.user, product_slug)
        skills = service.get_skills_list()
        return JsonResponse({'skills': skills})

class ExpertiseListView(LoginRequiredMixin, View):
    """View for retrieving expertise options for a skill."""
    
    def get(self, request, product_slug, skill_id):
        service = ChallengeAuthoringService(request.user, product_slug)
        expertise = service.get_expertise_for_skill(skill_id)
        return JsonResponse({'expertise': expertise})

class BountyModalView(LoginRequiredMixin, View):
    def get(self, request, product_slug):
        # Return bounty form template/data
        pass
        
    def post(self, request, product_slug):
        # Handle bounty creation/update
        pass
