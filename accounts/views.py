from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import JobSeekerSignUpForm, RecruiterSignUpForm
from django.contrib.auth import logout
from .models import JobSeekerProfile, RecruiterProfile
from .forms import JobSeekerProfileForm, RecruiterProfileForm, JobSeekerSignUpForm, RecruiterSignUpForm
from profiles.models import Profile
from django.contrib import messages


def signup(request):
    return render(request, "accounts/signup.html")


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Create a Profile if it doesn't exist
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                # Optional logic to mark recruiters automatically
                # Replace `some_logic_to_detect_recruiter` with your condition
                if user.email.endswith("@company.com"):  # Example condition
                    profile.is_recruiter = True
                    profile.company = "Default Company Name"  # optional
                    profile.save()

            login(request, user)
            return redirect("accounts:profile") 
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


# Recruiter signup
def recruiter_signup(request):
    if request.method == "POST":
        form = RecruiterSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully as a recruiter.")
            return redirect("accounts:login")  # or wherever you want
    else:
        form = RecruiterSignUpForm()
    return render(request, "accounts/signup_recruiter.html", {"form": form})


@login_required
def profile_view(request):
    user = request.user
    
    # Handle privacy settings update (POST request)
    if request.method == 'POST' and 'privacy' in request.POST:
        privacy_setting = request.POST.get('privacy')
        
        if hasattr(user, "jobseekerprofile"):
            profile = user.jobseekerprofile
            if privacy_setting in ['public','employers', 'private']:
                profile.privacy = privacy_setting
                profile.save()
        
        return redirect('accounts:profile')
    context = {}
    
    # Displays profile & account type
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

@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')  # send them back to login page

# Update privacy settings specifically for JobSeekers
@login_required
def update_privacy_settings(request):
    if request.method == 'POST':
        privacy_setting = request.POST.get('privacy')

        if hasattr(request.user, 'jobseekerprofile'):
            profile = request.user.jobseekerprofile
            if privacy_setting in ['public','employers', 'private']:
                profile.privacy = privacy_setting
                profile.save()
        
        return redirect('accounts:profile')
    
    return redirect('accounts:profile')

# Ability to edit profile (currently still separate from update privacy settings so can be fixed later)
@login_required
def edit_profile(request):
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
            return redirect("accounts:profile")
    else:
        form = form_class(instance=profile)

    return render(request, "accounts/edit_profile.html", {"form": form})
