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
from django.views import View
from django.views.generic import CreateView
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from django.urls import reverse
from apps.capabilities.product_management.models import Product, FileAttachment
from .forms import ChallengeAuthoringForm
from .services import ChallengeAuthoringService, RoleService
from apps.common.forms import AttachmentFormSet

class ChallengeAuthoringView(LoginRequiredMixin, CreateView):
    """Main view for challenge authoring flow."""
    form_class = ChallengeAuthoringForm
    template_name = 'challenge_authoring/main.html'

    def get_login_url(self):
        return reverse('security:sign_in')
    
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
        return render(request, 'challenge_authoring/main.html', context)
        
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
        return render(request, 'challenge_authoring/main.html', context)

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
    
    def get(self, request, *args, **kwargs):
        service = ChallengeAuthoringService(request.user, kwargs.get('product_slug'))
        skills = service.get_skills_list()
        return JsonResponse({'skills': skills})

class ExpertiseListView(LoginRequiredMixin, View):
    """View for retrieving expertise tree for a skill"""
    login_url = '/login/'
    
    def get(self, request, skill_id, *args, **kwargs):
        service = ChallengeAuthoringService(request.user, kwargs.get('product_slug'))
        expertise = service.get_expertise_for_skill(skill_id)
        return JsonResponse({'expertise': expertise})

class BountyModalView(LoginRequiredMixin, View):
    def get(self, request, product_slug):
        return JsonResponse({
            'status': 'success',
            'data': {}  # Add your modal data here
        })
        
    def post(self, request, product_slug):
        # Handle bounty creation/update
        pass
