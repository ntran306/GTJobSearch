from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Value, CharField
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json

from .forms import (
    JobSeekerProfileForm,
    RecruiterProfileForm,
    JobSeekerSignUpForm,
    RecruiterSignUpForm,
    EmailContactForm,
)

from communication.services import send_contact_email, render_safe_html

from .models import JobSeekerProfile, RecruiterProfile

# ---------- USER TYPE CHECKS ----------
def is_recruiter(user) -> bool:
    return hasattr(user, "recruiterprofile")

def is_jobseeker(user) -> bool:
    return hasattr(user, "jobseekerprofile")

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

# ---------- CONTACT EMAIL ----------
RATE_LIMIT_SECONDS = 60  # 1 email/minute per (sender, recipient) to prevent spam

@login_required
def view_profile(request, user_id: int):
    profile = (JobSeekerProfile.objects.select_related("user")
                  .filter(user_id=user_id).first()) \
              or get_object_or_404(RecruiterProfile.objects.select_related("user"), user_id=user_id)

    target_user = profile.user

    can_email = (request.user.id != user_id) and bool(target_user.email)
    if isinstance(profile, JobSeekerProfile):
        if profile.privacy == "private":
            can_email = False
        elif profile.privacy == "employers_only" and not is_recruiter(request.user):
            can_email = False

    # NEW: derive profile_type so profile.html renders the right blocks
    profile_type = "jobseeker" if isinstance(profile, JobSeekerProfile) else "recruiter"

    return render(request, "accounts/profile.html", {
        "profile": profile,
        "profile_type": profile_type,   # <—
        "can_email": can_email,
    })

@login_required
@require_http_methods(["GET", "POST"])
def contact_user(request, user_id: int):
    # Resolve target via your profiles (jobseeker or recruiter)
    profile = (JobSeekerProfile.objects.select_related("user")
                    .filter(user_id=user_id).first()) \
              or get_object_or_404(
                    RecruiterProfile.objects.select_related("user"),
                    user_id=user_id
                 )
    target_user = profile.user

    # don't allow emailing yourself or users without an email
    if target_user.id == request.user.id or not target_user.email:
        messages.error(request, "This user cannot be contacted.")
        return redirect("accounts:profile")

    # Enforce jobseeker privacy
    if isinstance(profile, JobSeekerProfile):
        if profile.privacy == "private":
            messages.error(request, "This user is not accepting messages.")
            return redirect("accounts:profile")
        if profile.privacy == "employers_only" and not is_recruiter(request.user):
            messages.error(request, "Only employers can contact this job seeker.")
            return redirect("accounts:profile")

    # rate-limit per (sender, recipient)
    rl_key = f"contact:{request.user.id}:{target_user.id}"

    if request.method == "POST":
        if cache.get(rl_key):
            messages.error(request, "Slow down—please wait a minute before sending another email.")
            return redirect(reverse("accounts:contact_user", args=[user_id]))

        form = EmailContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"].strip()
            message = form.cleaned_data["message"].strip()

            # Send via your Resend-backed service (matches your services.py!!)
            send_contact_email(
                to_email=target_user.email,
                subject=subject,
                message=message,
                reply_to=(request.user.email or None),
            )

            cache.set(rl_key, True, timeout=RATE_LIMIT_SECONDS)
            messages.success(request, "Your email was sent.")
            return redirect(reverse("accounts:view_profile", args=[user_id]))
    else:
        form = EmailContactForm()

    return render(request, "accounts/contact_user.html", {
        "form": form,
        "target_user": target_user,
        "profile": profile,
    })

# ---------- CONNECT PAGE (view other users) ----------
@login_required
def connect(request):
    """
    Browse Job Seekers & Recruiters with search/filter/pagination.
    Map pins are created from (lat/lng) if present; otherwise we geocode the location string on the client.
    Privacy rules:
      - JobSeeker: public visible to everyone; employers_only visible only to recruiters; private hidden.
    """
    user = request.user
    viewer_is_recruiter = hasattr(user, "recruiterprofile")

    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()           # "", "jobseeker", "recruiter"
    page = request.GET.get("page", "1")
    # location + radius come from the UI; server side distance filter is optional (we'll do client-side geofilter today)
    loc = request.GET.get("location", "").strip()
    radius = request.GET.get("radius", "").strip()
    lat = request.GET.get("lat", "").strip()
    lng = request.GET.get("lng", "").strip()

    # --- Job Seekers ---
    js_qs = JobSeekerProfile.objects.select_related("user").prefetch_related("skills")
    if viewer_is_recruiter:
        js_qs = js_qs.filter(privacy__in=["public", "employers_only"])
    else:
        js_qs = js_qs.filter(privacy="public")
    js_qs = js_qs.exclude(user_id=user.id)

    if q:
        js_qs = js_qs.filter(
            Q(user__username__icontains=q) |
            Q(headline__icontains=q) |
            Q(education__icontains=q) |
            Q(work_experience__icontains=q) |
            Q(skills__name__icontains=q)
        ).distinct()

    # --- Recruiters ---
    recruiters_qs = RecruiterProfile.objects.select_related("user").exclude(user_id=user.id)
    if q:
        recruiters_qs = recruiters_qs.filter(
            Q(user__username__icontains=q) |
            Q(company__icontains=q) |
            Q(name__icontains=q)
        )

    if role == "jobseeker":
        recruiters_qs = RecruiterProfile.objects.none()
    elif role == "recruiter":
        js_qs = JobSeekerProfile.objects.none()

    # Map to lightweight dicts for cards + markers.
    # If you later add latitude/longitude fields to profiles, include them here (and markers will be instant).
    def map_jobseeker(p):
        skill_names = ", ".join(p.skills.values_list("name", flat=True))
        # Try to read lat/lng if you add them later; else None
        lat_val = getattr(p, "latitude", None)
        lng_val = getattr(p, "longitude", None)
        return {
            "id": p.user_id,
            "username": p.user.username,
            "email": p.user.email,
            "headline": p.headline or "",
            "skills": skill_names,
            "location_text": p.location or "",
            "lat": float(lat_val) if lat_val is not None else None,
            "lng": float(lng_val) if lng_val is not None else None,
            "profile_type": "jobseeker",
        }

    def map_recruiter(p):
        lat_val = getattr(p, "latitude", None)   # if/when you add these fields
        lng_val = getattr(p, "longitude", None)
        return {
            "id": p.user_id,
            "username": p.user.username,
            "email": p.user.email,
            "headline": f"Recruiter at {p.company}" if p.company else "Recruiter",
            "skills": "",
            "location_text": getattr(p, "location", "") or "",   # if/when you add
            "lat": float(lat_val) if lat_val is not None else None,
            "lng": float(lng_val) if lng_val is not None else None,
            "profile_type": "recruiter",
            "company_or_school": p.company or "",
        }

    js_items = [map_jobseeker(p) for p in js_qs]
    rec_items = [map_recruiter(p) for p in recruiters_qs]
    items = js_items + rec_items
    items.sort(key=lambda x: x["username"].lower())

    # Paginator for cards
    paginator = Paginator(items, 12)
    page_obj = paginator.get_page(page)

    # Markers for all (not just current page) so the map shows the full picture — or switch to page_obj.object_list if you prefer.
    user_markers = []
    for it in items:
        user_markers.append({
            "id": it["id"],
            "name": it["username"],
            "role": it["profile_type"],
            "headline": it["headline"],
            "email": it["email"],
            "location_text": it["location_text"],
            "lat": it["lat"],
            "lng": it["lng"],
            "profileUrl": reverse("accounts:view_profile", args=[it["id"]]),
            "contactUrl": reverse("accounts:contact_user", args=[it["id"]]),
        })

    return render(request, "accounts/connect.html", {
        "page_obj": page_obj,
        "q": q,
        "role": role,
        "MAPS_KEY": settings.GOOGLE_MAPS_API_KEY,  # expose browser key only on this page
        "user_markers_json": json.dumps(user_markers),
        "lat": lat,
        "lng": lng,
        "radius": radius,
        "location": loc,
    })