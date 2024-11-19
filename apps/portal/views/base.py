"""Base views for the portal application."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from apps.capabilities.commerce.models import Organisation
from apps.capabilities.security.services import RoleService
from apps.portal.services.portal_services import PortalService, PortalError
from apps.capabilities.product_management.models import Product
from apps.capabilities.security.models import OrganisationPersonRoleAssignment
import logging

logger = logging.getLogger(__name__)

class PortalBaseView(LoginRequiredMixin, TemplateView):
    """Base view for portal pages."""
    def get_login_url(self):
        """Return the login URL for unauthenticated users."""
        return reverse('security:sign_in')
    
    portal_service = PortalService()
    role_service = RoleService()
    
    def get_current_organisation(self, request):
        """Get the current organisation from session or default to first available."""
        if not request.user.is_authenticated:
            return None
            
        current_org_id = request.session.get('current_organisation_id')
        person = request.user.person
        
        # Get user's organizations
        roles_summary = self.role_service.get_person_roles_summary(person)
        user_orgs = [item['organisation'] for item in roles_summary['organisations']]
        
        if user_orgs:
            if current_org_id:
                # Try to find the org from session
                current_org = next((org for org in user_orgs if org.id == current_org_id), None)
                if current_org:
                    return current_org
            # If no org in session or not found, default to first
            return user_orgs[0]
        return None
    
    def dispatch(self, request, *args, **kwargs):
        """Common permission checking and org context setting."""
        if not request.user.is_authenticated:
            return redirect(self.get_login_url())
            
        try:
            # Set current_organisation as an instance variable
            self.current_organisation = self.get_current_organisation(request)
            return super().dispatch(request, *args, **kwargs)
        except PortalError as e:
            return self.handle_service_error(e)
    
    def get_context_data(self, **kwargs):
        """Add common context data for all portal views."""
        context = super().get_context_data(**kwargs)
        try:
            person = self.request.user.person
            
            # Get current organisation from session
            current_org_id = self.request.session.get('current_organisation_id')
            logger.info(f"Current org ID from session: {current_org_id}")
            
            # Get all user organizations
            user_orgs = RoleService.get_user_organisations(person)
            
            # Get current org
            current_org = None
            if current_org_id:
                current_org = Organisation.objects.filter(id=current_org_id).first()
            if not current_org and user_orgs.exists():
                current_org = user_orgs.first()
                
            # Get current product slug from URL if available
            current_product_slug = None
            if 'product_slug' in self.kwargs:
                current_product_slug = self.kwargs['product_slug']
                
            logger.info(f"Current product slug: {current_product_slug}")
                
            # Get products specifically for the current organization
            organisation_products = []
            if current_org:
                organisation_products = RoleService.get_organisation_products(current_org)
                logger.info(f"Found {len(organisation_products)} products for org {current_org.name}")
            
            # Build the context dictionary
            context.update({
                'current_organisation': current_org,
                'user_organisations': user_orgs,
                'organisation_products': organisation_products,
                'current_product_slug': current_product_slug,
                'can_manage_org': current_org and RoleService.is_organisation_manager(
                    person, 
                    current_org
                ) if current_org else False,
                'is_authenticated': True,
                'user': self.request.user,
                'person': person,
            })
            
            # Add product-specific context if we have a product slug
            if current_product_slug:
                product = Product.objects.filter(slug=current_product_slug).first()
                if product:
                    context.update({
                        'current_product': product,
                        'can_manage_product': RoleService.has_product_management_access(
                            person,
                            product
                        ),
                    })
            
        except Exception as e:
            logger.error(f"Error in PortalBaseView.get_context_data: {str(e)}")
            messages.error(self.request, "Error loading portal context")
        return context
    
    def handle_service_error(self, error: PortalError):
        """Handle service layer errors consistently."""
        logger.error(f"Service error: {str(error)}")
        messages.error(self.request, str(error))
        return redirect('portal:dashboard')


class PortalDashboardView(PortalBaseView):
    """Dashboard view for portal."""
    template_name = "portal/dashboard.html"
    
    def get(self, request):
        """Handle GET request for dashboard."""
        try:
            # Get base context which includes user_products
            context = self.get_context_data()
            
            # Add dashboard-specific context
            dashboard_context = self.portal_service.get_dashboard_context(
                person=request.user.person
            )
            
            # Add analytics data if available
            if hasattr(self.portal_service, 'get_dashboard_analytics'):
                analytics = self.portal_service.get_dashboard_analytics(
                    person=request.user.person,
                    organisation=self.current_organisation
                )
                dashboard_context.update(analytics)
            
            context.update(dashboard_context)
            return render(request, self.template_name, context)
        except PortalError as e:
            return self.handle_service_error(e)


class PortalUserSettingsView(PortalBaseView):
    """View for user settings page."""
    template_name = 'portal/user_settings.html'

    def get(self, request):
        """Handle GET request for user settings."""
        context = self.get_context_data()
        context.update({
            'user': request.user,
            'person': request.user.person,
            'page_title': 'User Settings',
            'notifications_enabled': getattr(request.user, 'notifications_enabled', False),
        })
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for user settings updates."""
        try:
            # Update user settings logic here
            notifications_enabled = request.POST.get('notifications_enabled') == 'on'
            request.user.notifications_enabled = notifications_enabled
            request.user.save()
            
            messages.success(request, "Settings updated successfully")
            return redirect('portal:user-settings')
        except Exception as e:
            logger.error(f"Error updating user settings: {str(e)}")
            messages.error(request, "Failed to update settings")
            return redirect('portal:user-settings')

