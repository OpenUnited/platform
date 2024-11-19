"""Organisation-related views for the portal application."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.conf import settings
from apps.capabilities.commerce.models import Organisation
from apps.capabilities.security.models import OrganisationPersonRoleAssignment
from apps.capabilities.security.services import RoleService
from apps.portal.forms import (
    OrganisationSettingsForm,
    CreateOrganisationForm,
)
from .base import PortalBaseView
import logging

logger = logging.getLogger(__name__)

class OrganisationBaseView(PortalBaseView):
    """Base view for organisation-related views."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check organisation access and set session."""
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
        """Add organisation-specific context data."""
        context = super().get_context_data(**kwargs)
        if 'org_id' in self.kwargs:
            context['current_organisation_id'] = int(self.kwargs['org_id'])
        return context


class OrganisationListView(OrganisationBaseView):
    """View for listing user's organisations."""
    template_name = "portal/organisation/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user_organisations': RoleService.get_person_organisations_with_roles(
                self.request.user.person
            ),
            'page_title': "My Organisations",
            'can_create_org': True  # Add any specific logic for org creation permission
        })
        return context


class OrganisationDetailView(OrganisationBaseView):
    """View for organisation details and overview."""
    template_name = "portal/organisation/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = get_object_or_404(Organisation, id=self.kwargs['org_id'])
        person = self.request.user.person
        
        context.update({
            'organisation': organisation,
            'products': RoleService.get_organisation_products(organisation),
            'can_manage': RoleService.is_organisation_manager(person, organisation),
            'member_count': RoleService.get_organisation_members(organisation).count(),
            'page_title': organisation.name,
            'active_tab': 'overview'
        })
        return context


class OrganisationSettingsView(OrganisationBaseView):
    """View for managing organisation settings."""
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
            'page_title': f"Settings - {organisation.name}",
            'active_tab': 'settings'
        })
        return context

    def post(self, request, org_id):
        """Handle organisation settings updates."""
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
    """View for managing organisation members."""
    template_name = "portal/organisation/members.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs['org_id']
        organisation = get_object_or_404(Organisation, id=org_id)
        person = self.request.user.person
        
        if not RoleService.has_organisation_admin_rights(person, organisation):
            raise PermissionDenied("You must be an owner or manager to view organization members")
        
        context.update({
            'organisation': organisation,
            'members': RoleService.get_organisation_members(organisation),
            'can_manage': True,
            'page_title': f"Members - {organisation.name}",
            'active_tab': 'members'
        })
        return context


class CreateOrganisationView(PortalBaseView):
    """View for creating new organisations."""
    template_name = "portal/organisation/create.html"

    def get(self, request):
        """Display organisation creation form."""
        context = self.get_context_data()
        context.update({
            'form': CreateOrganisationForm(),
            'page_title': "Create Organisation"
        })
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle organisation creation."""
        form = CreateOrganisationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the organisation
                    organisation = form.save()
                    
                    # Assign owner role to creator
                    RoleService.assign_organisation_role(
                        person=request.user.person,
                        organisation=organisation,
                        role=OrganisationPersonRoleAssignment.OrganisationRoles.OWNER
                    )
                    
                    # Set as current organisation
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


class SwitchOrganisationView(OrganisationBaseView):
    """Handle switching between organisations."""
    
    def post(self, request, org_id):
        """Process organisation switch."""
        logger.info(f"Attempting to switch to organisation {org_id}")
        person = request.user.person
        organisation = get_object_or_404(Organisation, id=org_id)
        
        logger.info(f"Found organisation: {organisation.name}")
        
        # Debug current roles
        roles = RoleService.get_organisation_roles(person, organisation)
        logger.info(f"User roles for org: {[r.role for r in roles]}")
        
        # Verify user has access to this organisation
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
            
        # Update the session with the new organisation
        request.session['current_organisation_id'] = organisation.id
        request.session.modified = True
        
        messages.success(request, f"Switched to {organisation.name}")
        return redirect('portal:dashboard')
