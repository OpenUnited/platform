from django.shortcuts import render

def introduction(request):
    return render(request, "introduction.html")

def chapter1(request):
    return render(request, "chapter-1.html")