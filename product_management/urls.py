from django.urls import path

from .views import ChallengeListView, ProductListView

urlpatterns = [
    path("challenges/", ChallengeListView.as_view(), name="challenges"),
    path("products/", ProductListView.as_view(), name="products"),
]
