"""
URL configuration for the challenge authoring flow.

This module defines the URL patterns for the challenge authoring process,
including the main creation view and any auxiliary endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('expertise-options/', 
         views.ExpertiseOptionsView.as_view(), 
         name='challenge_expertise_options'),
    path('<str:product_slug>/challenge/create/', 
         views.ChallengeAuthoringView.as_view(), 
         name='create-challenge'),
]
