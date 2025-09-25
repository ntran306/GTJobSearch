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
            return redirect("/jobseeker/home")
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
            return redirect("/recruiter/home")
    else:
        form = RecruiterSignUpForm()
    return render(request, "accounts/recruiter_signup.html", {"form": form})

@login_required
def view_recruiter_profile(request):
    profile = request.user.recruiterprofile
    return render(request, "accounts/view_recruiter_profile.html", {"profile": profile})