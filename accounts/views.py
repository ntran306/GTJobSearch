from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import JobSeekerSignUpForm, RecruiterSignUpForm

def signup(request):
    return render(request, "accounts/signup.html")

def login_view(request):
    return render(request, "accounts/login.html")

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