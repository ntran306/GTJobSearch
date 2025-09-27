from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import JobSeekerSignUpForm, RecruiterSignUpForm
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404
from .models import JobSeekerProfile, RecruiterProfile



def signup(request):
    return render(request, "accounts/signup.html")

# ✅ Custom login view that actually logs in and redirects to jobs page
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/jobs/")  # 👈 Redirect to jobs page
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})

# Signup choice landing page
def signup_choice(request):
    return render(request, "accounts/signup_choice.html")

# Job Seeker signup
def jobseeker_signup(request):
    if request.method == "POST":
        form = JobSeekerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:profile")
    else:
        form = JobSeekerSignUpForm()
    return render(request, "accounts/jobseeker_signup.html", {"form": form})

@login_required
def view_jobseeker_profile(request):
    profile = request.user.jobseekerprofile
    return render(request, "accounts/view_jobseeker_profile.html", {"profile": profile})

# Recruiter signup
def recruiter_signup(request):
    if request.method == "POST":
        form = RecruiterSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:profile")
    else:
        form = RecruiterSignUpForm()
    return render(request, "accounts/recruiter_signup.html", {"form": form})

@login_required
def profile_view(request):
    user = request.user
    context = {}

    # Detect profile type
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

@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')  # send them back to login page