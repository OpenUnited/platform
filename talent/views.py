from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout

from .forms import SignUpForm, SignInForm


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


def sign_up(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("home")
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
