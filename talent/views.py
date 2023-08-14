from django import views
from django.shortcuts import HttpResponse, render


def profile(request):
    return render(request, "talent/profile.html")
