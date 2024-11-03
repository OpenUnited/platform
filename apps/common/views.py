from django.shortcuts import HttpResponse, render

import version


def home(request):
    return render(request, "home.html", context={"request": request})


def about(request):
    return render(request, "about.html", context={"request": request})


def privacy_policy(request):
    return render(request, "privacy_policy.html")


def terms_of_use(request):
    return render(request, "terms_of_use.html")


def enterprise_customers(request):
    return render(request, "enterprise_customers.html")


def custom_404_view(request, exception):
    return render(request, "404.html")


def version_view(request):
    return HttpResponse(f"Version Number: {version.version}")
