from django.shortcuts import render


def home(request):
    return render(request, "home.html", context={"request": request})


def custom_404_view(request, exception):
    return render(request, "404.html")
