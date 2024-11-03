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
from django.views.generic import View
from django.http import Http404, JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from apps.security.services import RoleService
from django.conf import settings
import json

from .forms import ChallengeAuthoringForm, BountyAuthoringForm
from .services import ChallengeAuthoringService
from apps.product_management.models import Product, FileAttachment, Challenge
from apps.talent.models import Skill, Expertise
from apps.common.forms import AttachmentFormSet

class ChallengeAuthoringView(LoginRequiredMixin, View):
    """Main view for challenge authoring flow."""
    form_class = ChallengeAuthoringForm
    template_name = 'main.html'
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        # Check authentication first (LoginRequiredMixin handles this)
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        # Check for person
        if not hasattr(request.user, 'person') or not request.user.person:
            return HttpResponseForbidden("User must have an associated person")
            
        # Get product and check manager OR admin role
        try:
            self.product = get_object_or_404(Product, slug=kwargs.get('product_slug'))
            role_service = RoleService()
            
            if not (role_service.is_product_manager(request.user.person, self.product) or 
                   role_service.is_product_admin(request.user.person, self.product)):
                return HttpResponseForbidden("Must be product manager or admin")
                
        except Http404:
            return HttpResponseNotFound("Product not found")
            
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        context = {
            'product': self.product,
            'form': self.form_class(product=self.product),
            'attachment_formset': AttachmentFormSet(queryset=FileAttachment.objects.none())
        }
        return render(request, 'main.html', context)
        
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, product=self.product)
        attachment_formset = AttachmentFormSet(
            request.POST, 
            request.FILES,
            queryset=FileAttachment.objects.none()
        )
        
        if form.is_valid() and attachment_formset.is_valid():
            challenge = form.save(commit=False)
            challenge.product = self.product
            challenge.save()
            
            # Save attachments
            attachments = attachment_formset.save(commit=False)
            for attachment in attachments:
                attachment.challenge = challenge
                attachment.save()
                
            return redirect(challenge.get_absolute_url())
            
        context = {
            'product': self.product,
            'form': form,
            'attachment_formset': attachment_formset
        }
        return render(request, 'main.html', context)

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
        except Skill.DoesNotExist:
            return HttpResponseNotFound("Skill not found")
            
        expertise = Expertise.objects.filter(
            skill=skill,
            selectable=True
        ).order_by('name').values('id', 'name')
        
        return JsonResponse({'expertise': list(expertise)})

class BountyModalView(LoginRequiredMixin, View):
    def get(self, request, product_slug):
        return JsonResponse({
            'status': 'success',
            'data': {}  # Add your modal data here
        })
        
    def post(self, request, product_slug):
        # Handle bounty creation/update
        pass
