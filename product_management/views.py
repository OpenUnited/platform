from django.shortcuts import render
from django.views.generic import ListView

from .models import Challenge


class ChallengeListView(ListView):
    model = Challenge
    context_object_name = "challenges"
    template_name = "product_management/challenges.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
