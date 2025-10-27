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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from jobs.models import Skill

from .forms import (
    JobSeekerProfileForm,
    RecruiterProfileForm,
    JobSeekerSignUpForm,
    RecruiterSignUpForm,
    EmailContactForm,
)

from communication.services import send_contact_email, render_safe_html

from .models import JobSeekerProfile, RecruiterProfile

# ---------- USER TYPE CHECKS & GET USERID ----------
def is_recruiter(user) -> bool:
    return hasattr(user, "recruiterprofile")

def is_jobseeker(user) -> bool:
    return hasattr(user, "jobseekerprofile")

def _get_profile_for_user_id(user_id: int):
    js = JobSeekerProfile.objects.select_related("user").filter(user_id=user_id).first()
    if js:
        return js
    return get_object_or_404(RecruiterProfile.objects.select_related("user"), user_id=user_id)

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

    skills = Skill.objects.all()

    return render(request, "accounts/jobseeker_signup.html", {
        "form": form,
        "skills": skills,  # required for {{ skills|json_script }}
    })

# ----------- Skills Creating ---------------
@require_http_methods(["POST"])
def create_skill(request):
    """API endpoint to create a new skill"""
    try:
        data = json.loads(request.body)
        skill_name = data.get('name', '').strip()
        
        if not skill_name:
            return JsonResponse({'error': 'Skill name is required'}, status=400)
        
        # Create or get existing skill
        skill, created = Skill.objects.get_or_create(name=skill_name)
        
        return JsonResponse({
            'id': skill.id,
            'name': skill.name,
            'created': created
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
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
# OWN PROFILE
@login_required
def profile_view(request):
    owner = request.user

    # Handle privacy updates (job seekers)
    if request.method == "POST" and "privacy" in request.POST:
        privacy_setting = (request.POST.get("privacy") or "").lower()
        if hasattr(owner, "jobseekerprofile") and privacy_setting in {"public", "employers_only", "employers", "private"}:
            if privacy_setting == "employers":
                privacy_setting = "employers_only"
            owner.jobseekerprofile.privacy = privacy_setting
            owner.jobseekerprofile.save()
            messages.success(request, "Privacy settings updated.")
        return redirect("accounts:profile")

    if hasattr(owner, "jobseekerprofile"):
        profile = owner.jobseekerprofile
        profile_type = "jobseeker"
    elif hasattr(owner, "recruiterprofile"):
        profile = owner.recruiterprofile
        profile_type = "recruiter"
    else:
        profile = None
        profile_type = None

    return render(request, "accounts/profile.html", {
        "owner": owner,
        "is_owner": True,
        "profile": profile,
        "profile_type": profile_type,
        "can_email": False, # never email yourself
        "saved_jobs": [] if profile_type == "jobseeker" else None,
    })


# ---------- EDIT PROFILE ----------
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

# VIEW OTHER USER'S PROFILE
@login_required
def view_profile(request, user_id: int):
    profile = _get_profile_for_user_id(user_id)
    owner = profile.user

    can_email = (request.user.id != owner.id) and bool(owner.email)
    if isinstance(profile, JobSeekerProfile):
        privacy = (profile.privacy or "").lower()
        if privacy == "private":
            can_email = False
        elif privacy in {"employers_only", "employers"} and not is_recruiter(request.user):
            can_email = False

    return render(request, "accounts/profile.html", {
        "owner": owner,
        "is_owner": owner.id == request.user.id,
        "profile": profile,
        "profile_type": "jobseeker" if isinstance(profile, JobSeekerProfile) else "recruiter",
        "can_email": can_email,
    })

@login_required
@require_http_methods(["GET", "POST"])
def contact_user(request, user_id: int):
    profile = _get_profile_for_user_id(user_id)
    target_user = profile.user

    # Guards
    if (target_user.id == request.user.id) or (not target_user.email):
        messages.error(request, "This user cannot be contacted.")
        return redirect("accounts:view_profile", user_id=user_id)

    if isinstance(profile, JobSeekerProfile):
        privacy = (profile.privacy or "").lower()
        if privacy == "private":
            messages.error(request, "This user is not accepting messages.")
            return redirect("accounts:view_profile", user_id=user_id)
        if privacy in {"employers_only", "employers"} and not is_recruiter(request.user):
            messages.error(request, "Only employers can contact this job seeker.")
            return redirect("accounts:view_profile", user_id=user_id)

    # Rate-limit
    rl_key = f"contact:{request.user.id}:{target_user.id}"
    if cache.get(rl_key):
        messages.error(request, "Please wait a minute before sending another email.")
        return redirect("accounts:view_profile", user_id=user_id)

    # Pull fields from the inline form on the profile page
    subject = (request.POST.get("subject") or "").strip()
    message = (request.POST.get("message") or "").strip()
    if not subject or not message:
        messages.error(request, "Subject and message are required.")
        return redirect("accounts:view_profile", user_id=user_id)

    # Send
    try:
        send_contact_email(
            to_email=target_user.email,
            subject=subject,
            message=message,
            reply_to=(request.user.email or None),
        )
        cache.set(rl_key, True, timeout=RATE_LIMIT_SECONDS)
        messages.success(request, f"Email sent to {target_user.username}.")
    except Exception as e:
        messages.error(request, f"Failed to send email: {e}")

    return redirect("accounts:view_profile", user_id=user_id)

# ---------- CONNECT PAGE (view other users) ----------
@login_required
def connect(request):
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