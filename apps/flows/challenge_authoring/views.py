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
        
        # Get Person instance for the user
        try:
            person = request.user.person
            logger.debug(f"Found person: {person}")
        except Person.DoesNotExist:
            logger.error(f"No Person instance found for user {request.user}")
            return JsonResponse({
                'status': 'error',
                'message': 'User profile not found'
            }, status=400)
        
        form = self.form_class(request.POST, product=self.product, user=request.user)
        attachment_formset = AttachmentFormSet(
            request.POST, 
            request.FILES,
            queryset=FileAttachment.objects.none()
        )
        
        # Attach request to form for bounty validation
        form.request = request
        
        # Log validation process
        logger.debug("Starting form validation")
        form_valid = form.is_valid()
        logger.debug(f"Form is_valid(): {form_valid}")
        logger.debug(f"Form errors: {form.errors}")
        logger.debug(f"Form cleaned data: {form.cleaned_data if form_valid else None}")
        
        formset_valid = attachment_formset.is_valid()
        logger.debug(f"Formset is_valid(): {formset_valid}")
        logger.debug(f"Formset errors: {attachment_formset.errors}")
        
        if form_valid and formset_valid:
            logger.debug("Both form and formset are valid, proceeding with challenge creation")
            try:
                # Get product slug from kwargs
                product_slug = kwargs.get('product_slug')
                logger.debug(f"Using product slug: {product_slug}")
                
                service = ChallengeAuthoringService(
                    user=request.user,
                    product_slug=product_slug
                )
                
                challenge = service.create_challenge_with_bounties(
                    challenge_data=form.cleaned_data,
                    user=person,
                    request=request  # Service will get bounties from session
                )
                
                # Save attachments if any
                attachments = attachment_formset.save()
                if attachments:
                    challenge.attachments.add(*attachments)
                    logger.debug(f"Added {len(attachments)} attachments to challenge {challenge.id}")
                
                # Clear session after successful creation
                if 'pending_bounties' in request.session:
                    del request.session['pending_bounties']
                    
                return JsonResponse({
                    'status': 'success',
                    'redirect_url': challenge.get_absolute_url()
                })
                
            except Exception as e:
                logger.error(f"Error creating challenge: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
        else:
            # Initialize errors dict
            errors = {}
            
            # Add form errors if any
            if form.errors:
                errors.update(form.errors)
                
            # Add formset errors if any
            if attachment_formset.errors:
                errors['attachments'] = attachment_formset.errors
                
            logger.error(f"Validation failed. Combined errors: {errors}")
            return JsonResponse({
                'status': 'error',
                'errors': errors
            }, status=400)

        logger.debug("==================== END POST REQUEST ====================")

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
    logger.debug("==================== START BOUNTY TABLE UPDATE ====================")
    try:
        data = json.loads(request.body)
        logger.debug(f"Received Data: {data}")
        bounties = data.get('bounties', [])
        logger.debug(f"Extracted Bounties: {bounties}")
        
        # Update session
        request.session['pending_bounties'] = bounties
        request.session.modified = True
        logger.debug(f"Updated Session Bounties: {request.session.get('pending_bounties')}")
        
        response = render(request, 'challenge_authoring/components/bounty_table.html', {
            'bounties': bounties
        })
        logger.debug("Successfully rendered bounty table")
        logger.debug("==================== END BOUNTY TABLE UPDATE ====================")
        return response

    except Exception as e:
        logger.exception("Error in bounty_table view")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

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
