"""Client and worker account registration."""
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from accounts.forms.auth import SignUpForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("skillserve_dashboard")
    initial_role = request.GET.get("role", "")
    if initial_role not in dict(SignUpForm.base_fields["role"].choices):
        initial_role = ""
    form = SignUpForm(request.POST if request.method == "POST" else None, initial={"role": initial_role})
    if request.method == "POST" and form.is_valid():
        user = form.save()
        if user.role == "worker":
            login(request, user)
            messages.success(request, "Welcome! Complete your worker profile and submit it for verification.")
            return redirect("edit_worker_profile")
        messages.success(request, "Your account has been created. Log in to get started.")
        return redirect("login")
    return render(request, "accounts/signup.html", {"form": form})
