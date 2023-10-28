from django.urls import path
from . import views

urlpatterns = [
    path("", views.introduction, name="introduction"),
    path("chapter-1/", views.chapter1, name="chapter1"),
]