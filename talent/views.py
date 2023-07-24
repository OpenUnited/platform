from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import Profile
from .forms import SignUpForm, SignInForm, ProfileDetailsForm


def sign_in(request):
    if request.method == "POST":
        form = SignInForm(request.POST)
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            form.add_error(None, "Invalid credentials")
    else:
        form = SignInForm()

    return render(request, "talent/sign_in.html", {"form": form})


# TODO: add unauthorized page when someone tries to reach this view
# TODO: saving photos does not work right now, fix it
@login_required
def complete_profile(request):
    if request.method == "POST":
        form = ProfileDetailsForm(request.POST)
        if form.is_valid():
            username = request.user.username
            talent = Profile.objects.get(username=username)
            talent.headline = form.cleaned_data.get("headline")
            talent.overview = form.cleaned_data.get("overview")
            talent.photo = form.cleaned_data.get("photo")
            talent.save()

            return redirect("home")
    return render(
        request, "talent/sign_up_details.html", {"form": ProfileDetailsForm()}
    )


def sign_up(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("complete_profile")
        else:
            return render(request, "talent/sign_up.html", {"form": form})

    form = SignUpForm()
    return render(request, "talent/sign_up.html", {"form": form})


def log_out(request):
    logout(request)
    return redirect("home")


def reset_password(request):
    return HttpResponse(
        "Implement this page. Check if Django provides the necessary functions"
    )
