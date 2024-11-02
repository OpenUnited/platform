"""
Views for the ideas and bugs management flow.

This module handles the presentation layer for product ideas and bugs,
including creation, updates, voting, and listing functionality.
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
from django.http import HttpResponse
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

from apps.product_management.models import Bug, Idea, IdeaVote, Product
from apps.product_management import utils
from apps.product_management.forms import IdeaForm, BugForm

class ProductIdeasAndBugsView(utils.BaseProductDetailView, TemplateView):
    """Combined view for displaying both ideas and bugs for a product."""
    template_name = "product_management/product_ideas_bugs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]

        ideas = Idea.objects.filter(product=product)
        bugs = Bug.objects.filter(product=product)

        context.update({
            "ideas": ideas,
            "bugs": bugs,
        })
        return context

class CreateProductIdea(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    """View for creating new product ideas."""
    login_url = "sign_in"
    template_name = "product_management/add_product_idea.html"
    form_class = IdeaForm

    def post(self, request, *args, **kwargs):
        form = IdeaForm(request.POST)

        if form.is_valid():
            person = self.request.user.person
            product = Product.objects.get(slug=kwargs.get("product_slug"))

            idea = form.save(commit=False)
            idea.person = person
            idea.product = product
            idea.save()

            return redirect("product_ideas_bugs", **kwargs)

        return super().post(request, *args, **kwargs)

class ProductIdeaDetail(utils.BaseProductDetailView, DetailView):
    """Detail view for a product idea."""
    template_name = "product_management/product_idea_detail.html"
    model = Idea
    context_object_name = "idea"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "pk": self.object.pk,
        })

        if self.request.user.is_authenticated:
            context.update({
                "actions_available": self.object.person == self.request.user.person,
            })
        else:
            context.update({"actions_available": False})

        return context

class UpdateProductIdea(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    """View for updating existing product ideas."""
    login_url = "sign_in"
    template_name = "product_management/update_product_idea.html"
    model = Idea
    form_class = IdeaForm

    def get(self, request, *args, **kwargs):
        idea = self.get_object()
        if idea.person != self.request.user.person:
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        idea = self.get_object()
        if idea.person != self.request.user.person:
            raise PermissionDenied

        form = IdeaForm(request.POST, instance=idea)
        if form.is_valid():
            form.save()
            return redirect("product_idea_detail", **kwargs)

        return super().post(request, *args, **kwargs)

@login_required(login_url="sign_in")
def cast_vote_for_idea(request, pk):
    """Handle voting/unvoting for ideas."""
    idea = Idea.objects.get(pk=pk)
    if IdeaVote.objects.filter(idea=idea, voter=request.user).exists():
        IdeaVote.objects.get(idea=idea, voter=request.user).delete()
    else:
        IdeaVote.objects.create(idea=idea, voter=request.user)
    return HttpResponse(IdeaVote.objects.filter(idea=idea).count())

class CreateProductBug(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    """View for creating new product bugs."""
    login_url = "sign_in"
    template_name = "product_management/add_product_bug.html"
    form_class = BugForm

    def post(self, request, *args, **kwargs):
        form = BugForm(request.POST)

        if form.is_valid():
            person = self.request.user.person
            product = Product.objects.get(slug=kwargs.get("product_slug"))

            bug = form.save(commit=False)
            bug.person = person
            bug.product = product
            bug.save()

            return redirect("product_ideas_bugs", **kwargs)

        return super().post(request, *args, **kwargs)

class ProductBugDetail(utils.BaseProductDetailView, DetailView):
    """Detail view for a product bug."""
    template_name = "product_management/product_bug_detail.html"
    model = Bug
    context_object_name = "bug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "pk": self.object.pk,
        })

        if self.request.user.is_authenticated:
            context.update({
                "actions_available": self.object.person == self.request.user.person,
            })
        else:
            context.update({"actions_available": False})

        return context

class UpdateProductBug(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    """View for updating existing product bugs."""
    login_url = "sign_in"
    template_name = "product_management/update_product_bug.html"
    model = Bug
    form_class = BugForm

    def get(self, request, *args, **kwargs):
        bug = self.get_object()
        if bug.person != self.request.user.person:
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        bug = self.get_object()
        if bug.person != self.request.user.person:
            raise PermissionDenied

        form = BugForm(request.POST, instance=bug)
        if form.is_valid():
            form.save()
            return redirect("product_bug_detail", **kwargs)

        return super().post(request, *args, **kwargs)
