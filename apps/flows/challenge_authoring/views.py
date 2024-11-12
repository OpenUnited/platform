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
from apps.capabilities.product_management.models import Product, FileAttachment, Bounty
from .forms import ChallengeAuthoringForm, BountyAuthoringForm
from .services import ChallengeAuthoringService, RoleService
from apps.common.forms import AttachmentFormSet
from apps.capabilities.talent.services import SkillService
import logging
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import json
from django.db import transaction
from apps.capabilities.talent.models import Person
import uuid
from django.views.decorators.csrf import csrf_exempt  # Temporary for debugging

# Create a named logger for this module
logger = logging.getLogger(__name__)
# Set the log level
logger.setLevel(logging.DEBUG)

class ChallengeAuthoringView(LoginRequiredMixin, CreateView):
    """Main view for challenge authoring flow."""
    form_class = ChallengeAuthoringForm
    template_name = 'challenge_authoring/main.html'

    def get_login_url(self):
        return reverse('security:sign_in')
    
    def dispatch(self, request, *args, **kwargs):
        logger.error("DEBUG - dispatch called")
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
        logger.error("DEBUG - get called")
        
        # Create bounty form with initial data
        initial = {'product': self.product}
        bounty_form = BountyAuthoringForm(initial=initial)
        
        context = {
            'product': self.product,
            'form': self.form_class(product=self.product, user=request.user),
            'bounty_form': bounty_form,
            'attachment_formset': AttachmentFormSet(queryset=FileAttachment.objects.none())
        }
        return render(request, 'challenge_authoring/main.html', context)
        
    def post(self, request, *args, **kwargs):
        logger.debug("==================== START POST REQUEST ====================")
        
        try:
            person = request.user.person
            logger.debug(f"Found person: {person}")
            
            logger.debug("Starting form validation")
            form = ChallengeAuthoringForm(request.POST, product=self.product, user=request.user)
            formset = AttachmentFormSet(request.POST, request.FILES)
            
            if form.is_valid() and formset.is_valid():
                logger.debug("Form and formset are valid")
                
                # Use the service to create the challenge with bounties
                service = ChallengeAuthoringService(request.user, self.kwargs.get('product_slug'))
                challenge = service.create_challenge_with_bounties(
                    challenge_data=form.cleaned_data,
                    person=person,
                    request=request
                )
                
                return JsonResponse({
                    'status': 'success',
                    'redirect_url': reverse('product_management:challenge-detail', kwargs={
                        'product_slug': challenge.product.slug,
                        'pk': challenge.id
                    })
                })
                
            else:
                logger.error(f"Form errors: {form.errors}")
                logger.error(f"Formset errors: {formset.errors}")
                return JsonResponse({
                    'status': 'error',
                    'errors': {
                        'form': form.errors,
                        'formset': formset.errors
                    }
                }, status=400)
                
        except Exception as e:
            logger.exception("Error in challenge creation")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    def get_success_url(self):
        return reverse('product_challenges', kwargs={'product_slug': self.kwargs['product_slug']})

    def get_context_data(self, **kwargs):
        logger.error("DEBUG - get_context_data starting")
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        
        # Add debug logging for product and slug
        logger.error(f"DEBUG - Product: {self.product}")
        logger.error(f"DEBUG - Product Slug: {self.kwargs.get('product_slug')}")
        
        # Create bounty form and debug its contents
        bounty_form = BountyAuthoringForm()
        logger.error(f"DEBUG - Bounty form created with {bounty_form.fields['skill'].queryset.count()} skills")
        
        # Debug skill queryset
        skill_queryset = bounty_form.fields['skill'].queryset
        print(f"Skill queryset type: {type(skill_queryset)}")
        print(f"Skills count: {skill_queryset.count()}")
        
        if skill_queryset:
            first_skills = list(skill_queryset[:3])
            print(f"First few skills: {first_skills}")
        else:
            print("No skills found in queryset")
            
        # Update context
        context.update({
            'product': self.product,
            'product_slug': self.kwargs.get('product_slug'),
            'form': self.form_class(product=self.product, user=self.request.user),
            'bounty_form': bounty_form,
            'attachment_formset': AttachmentFormSet(queryset=FileAttachment.objects.none())
        })
        logger.error("DEBUG - get_context_data finished")
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

@require_http_methods(["POST"])
def bounty_table(request, product_slug):
    try:
        data = json.loads(request.body)
        bounties = data.get('bounties', [])
        
        logger.debug(f"Received bounties: {bounties}")
        
        return render(request, 'challenge_authoring/components/bounty_table.html', {
            'bounties': bounties
        })
    except Exception as e:
        logger.exception("Error processing bounties")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def remove_bounty(request, bounty_id):
    logger.info(f"Removing bounty {bounty_id}")
    bounties = request.session.get('pending_bounties', [])
    bounties = [b for b in bounties if b['id'] != bounty_id]
    request.session['pending_bounties'] = bounties
    request.session.modified = True
    
    logger.info(f"Updated bounties after removal: {bounties}")
    
    return render(request, 'challenge_authoring/components/bounty_table.html', {
        'bounties': bounties
    })

@require_http_methods(["GET", "POST"])
def create(request, product_slug):
    if request.method == "POST":
        logger.debug("==================== START POST REQUEST ====================")
        
        try:
            # Get bounties from POST data
            bounties_json = request.POST.get('bounties')
            logger.debug(f"Received bounties: {bounties_json}")
            
            form = ChallengeAuthoringForm(request.POST)
            
            if form.is_valid():
                challenge = form.save(commit=False)
                challenge.product = get_object_or_404(Product, slug=product_slug)
                challenge.created_by = request.person
                challenge.save()
                
                # Save bounties
                bounties = form.cleaned_data['bounties']
                for bounty_data in bounties:
                    bounty = Bounty(
                        challenge=challenge,
                        skill_id=bounty_data['skill']['id'],
                        title=bounty_data['title'],
                        description=bounty_data['description'],
                        points=bounty_data['points']
                    )
                    bounty.save()
                
                return JsonResponse({
                    'status': 'success',
                    'redirect_url': reverse('challenge_detail', kwargs={
                        'product_slug': product_slug,
                        'challenge_id': challenge.id
                    })
                })
            else:
                logger.error(f"Form validation errors: {form.errors}")
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
                
        except Exception as e:
            logger.exception("Error creating challenge")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    # Your existing GET logic...
