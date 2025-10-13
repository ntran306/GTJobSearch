from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User

from .forms import (
    JobSeekerProfileForm,
    RecruiterProfileForm,
    JobSeekerSignUpForm,
    RecruiterSignUpForm,
)
from .models import JobSeekerProfile, RecruiterProfile


# ---------- SIGNUP CHOICE PAGE ----------
def signup_choice(request):
    """Landing page where user chooses job seeker or recruiter"""
    return render(request, "accounts/signup_choice.html")


# ---------- JOB SEEKER SIGNUP ----------
from .forms import JobSeekerSignUpForm, RecruiterSignUpForm

def jobseeker_signup(request):
    if request.method == "POST":
        form = JobSeekerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully as a job seeker.")
            return redirect("home:index")
    else:
        form = JobSeekerSignUpForm()
    return render(request, "accounts/jobseeker_signup.html", {"form": form})

# ---------- RECRUITER SIGNUP ----------
def recruiter_signup(request):
    if request.method == "POST":
        form = RecruiterSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully as a recruiter.")
            return redirect("home:index")
    else:
        form = RecruiterSignUpForm()
    return render(request, "accounts/recruiter_signup.html", {"form": form})



# ---------- LOGIN ----------
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Log the user in and redirect to their profile page
            login(request, user)
            return redirect("accounts:profile")
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


# ---------- LOGOUT ----------
@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


# ---------- PROFILE VIEW ----------
@login_required
def profile_view(request):
    user = request.user

    # Handle privacy updates (for job seekers)
    if request.method == "POST" and "privacy" in request.POST:
        privacy_setting = request.POST.get("privacy")
        if hasattr(user, "jobseekerprofile") and privacy_setting in [
            "public",
            "employers_only",
            "private",
        ]:
            user.jobseekerprofile.privacy = privacy_setting
            user.jobseekerprofile.save()
        return redirect("accounts:profile")

    # Determine which type of profile to show
    context = {}
    if hasattr(user, "jobseekerprofile"):
        context["profile_type"] = "jobseeker"
        context["profile"] = user.jobseekerprofile
        context["saved_jobs"] = []
    elif hasattr(user, "recruiterprofile"):
        context["profile_type"] = "recruiter"
        context["profile"] = user.recruiterprofile
    else:
        context["profile_type"] = None
        context["profile"] = None

    return render(request, "accounts/profile.html", context)


# ---------- EDIT PROFILE ----------
@login_required
def edit_profile(request):
    """Universal edit profile view — decides form based on user type"""
    user = request.user

    if hasattr(user, "jobseekerprofile"):
        profile = user.jobseekerprofile
        form_class = JobSeekerProfileForm
    elif hasattr(user, "recruiterprofile"):
        profile = user.recruiterprofile
        form_class = RecruiterProfileForm
    else:
        return redirect("accounts:profile")  # fallback if no profile

    if request.method == "POST":
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = form_class(instance=profile)

    return render(request, "accounts/edit_profile.html", {"form": form})


# ---------- OPTIONAL SEPARATE RECRUITER EDIT ----------
@login_required
def edit_recruiter_profile(request):
    profile = getattr(request.user, "recruiterprofile", None)
    if not profile:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RecruiterProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Recruiter profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = RecruiterProfileForm(instance=profile)

    return render(request, "accounts/edit_recruiter_profile.html", {"form": form})
