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
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from apps.security.services import RoleService
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
import json

from .forms import ChallengeAuthoringForm, BountyAuthoringForm
from .services import ChallengeAuthoringService
from apps.product_management.models import Product
from apps.talent.models import Skill, Expertise

class ChallengeAuthoringView(LoginRequiredMixin, View):
    """Main view for challenge authoring flow."""
    form_class = ChallengeAuthoringForm
    template_name = 'main.html'
    login_url = '/login/'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.product = get_object_or_404(Product, slug=kwargs.get('product_slug'))
        self.role_service = RoleService()

    def dispatch(self, request, *args, **kwargs):
        # First check authentication (handled by LoginRequiredMixin)
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        # Then check for person
        if not hasattr(request.user, 'person') or not request.user.person:
            return HttpResponseForbidden("User must have an associated person")
            
        # Finally check product manager role
        if not self.role_service.is_product_manager(request.user.person, self.product):
            return HttpResponseForbidden("Must be product manager")
            
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        return render(request, 'challenge_authoring/main.html')
        
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            service = ChallengeAuthoringService(request.user, self.product.slug)
            success, challenge, errors = service.create_challenge(
                {k: v for k, v in data.items() if k != 'bounties'},
                data.get('bounties', [])
            )
            
            if success:
                return JsonResponse({'redirect_url': challenge.get_absolute_url()})
            return JsonResponse({'errors': errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'errors': 'Invalid JSON'}, status=400)

    def get_success_url(self):
        return reverse('product_challenges', kwargs={'product_slug': self.kwargs['product_slug']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)

class SkillsListView(LoginRequiredMixin, View):
    """View for retrieving skills list"""
    login_url = '/login/'
    
    def get(self, request, product_slug):
        skills = Skill.objects.all().values('id', 'name')
        return JsonResponse({'skills': list(skills)})

class ExpertiseListView(LoginRequiredMixin, View):
    """View for retrieving expertise tree for a skill"""
    login_url = '/login/'
    
    def get(self, request, product_slug, skill_id):
        try:
            skill = Skill.objects.get(id=skill_id)
            expertise = Expertise.objects.filter(
                skill=skill,
                selectable=True
            ).values('id', 'name')
            return JsonResponse({'expertise': list(expertise)})
        except Skill.DoesNotExist:
            return HttpResponseNotFound('Skill not found')

class BountyModalView(LoginRequiredMixin, View):
    def get(self, request, product_slug):
        return JsonResponse({
            'status': 'success',
            'data': {}  # Add your modal data here
        })
        
    def post(self, request, product_slug):
        # Handle bounty creation/update
        pass
