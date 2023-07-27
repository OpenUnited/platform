from django.urls import path

from .views import ChallengeListView

urlpatterns = [path("challenges/", ChallengeListView.as_view(), name="challenges")]
