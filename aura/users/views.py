from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SignUpForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = SignUpForm()

    return render(request, "users/signup.html", {"form": form})


@login_required
def dashboard(request):
    if getattr(request.user, "is_professor", None) and request.user.is_professor():
        return redirect("professor_overview")
    return redirect("aluno_overview")

from django.shortcuts import render

# Create your views here.
