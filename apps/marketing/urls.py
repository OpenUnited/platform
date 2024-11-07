from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'marketing'

urlpatterns = [
    # Landing pages
    path('', TemplateView.as_view(template_name='landing-pages/index.html'), name='index'),
    path('about/', TemplateView.as_view(template_name='landing-pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='landing-pages/contact.html'), name='contact'),
    path('enterprise-support/', TemplateView.as_view(template_name='landing-pages/enterprise-support.html'), name='enterprise_support'),
    path('features/', TemplateView.as_view(template_name='landing-pages/features.html'), name='features'),
    path('how-it-works/', TemplateView.as_view(template_name='landing-pages/how-it-works.html'), name='how_it_works'),
    path('why-openunited/', TemplateView.as_view(template_name='landing-pages/why-openunited.html'), name='why_openunited'),
    
    # Legacy content pages (keeping these for backward compatibility)
    path('c/about/', TemplateView.as_view(template_name='landing-pages/about.html'), name='legacy_about'),
    path('c/enterprise-customers/', TemplateView.as_view(template_name='landing-pages/enterprise-customers.html'), name='enterprise_customers'),
    path('c/privacy-policy/', TemplateView.as_view(template_name='landing-pages/privacy.html'), name='privacy_policy'),
    path('c/terms/', TemplateView.as_view(template_name='landing-pages/terms.html'), name='terms'),
    path('c/terms/', TemplateView.as_view(template_name='landing-pages/terms.html'), name='terms_of_use'),
    path('c/<path:path>', views.MarketingPageView.as_view(), name='marketing_page'),
]
