from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.conf import settings
from .models import Job, Skill
from .utils import haversine, batch_road_distance_and_time
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib.auth.decorators import login_required
from .forms import JobForm
from django.contrib import messages
from django.http import HttpResponse
from accounts.models import RecruiterProfile
from functools import wraps

def index(request):
    pay_type = request.GET.get("pay_type")
    min_salary = request.GET.get("min_salary")
    max_salary = request.GET.get("max_salary")
    skills_filter = request.GET.getlist('skills')  # Get skills filter

    jobs = Job.objects.all()

    # Name and company filter
    search = request.GET.get("search")
    if search:
        jobs = jobs.filter(Q(title__icontains=search) | Q(company__icontains=search))


    # Pay type filter
    pay_type = request.GET.get("pay_type")
    if pay_type and pay_type != "all":
        jobs = jobs.filter(pay_type=pay_type)

    # Salary filter
    min_salary = request.GET.get("min_salary")
    max_salary = request.GET.get("max_salary")
    if min_salary:
        try:
            jobs = jobs.filter(pay_min__gte=float(min_salary))
        except ValueError:
            pass
    if max_salary:
        try:
            jobs = jobs.filter(pay_max__lte=float(max_salary))
        except ValueError:
            pass

    # Visa sponsorship filter
    visa = request.GET.get("visa")  # could be "on" if checkbox is checked
    if visa == "on":
        jobs = jobs.filter(visa_sponsorship=True)

    # Filter by skills
    if skills_filter and skills_filter != ['']:
        jobs = jobs.filter(
            Q(required_skills__name__in=skills_filter) | 
            Q(preferred_skills__name__in=skills_filter)
        ).distinct()

    # Get all skills for the dropdown
    all_skills = Skill.objects.all().order_by('name')

    # Radius and location filter (use road distance/time instead of pure haversine)
    radius = request.GET.get("radius")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    location_text = (request.GET.get("location") or "").strip()

    # Remote location mode (typed in location box)
    remote_tokens = {"remote", "wfh", "work from home", "anywhere", "fully remote", "remote only"}
    is_remote_search = location_text.lower() in remote_tokens

    # Convert queryset to list so we can attach display-only attributes like road_miles / drive_minutes
    jobs = list(jobs)

    if is_remote_search:
        # If your model has a boolean is_remote, include it; otherwise, fall back to location text matches
        remote_q = (
            Q(location__icontains="remote") |
            Q(location__icontains="work from home") |
            Q(location__icontains="wfh") |
            Q(location__icontains="anywhere")
        )
        if hasattr(Job, "is_remote"):
            remote_q = Q(is_remote=True) | remote_q

        # Filter the *list* based on queryset membership
        remote_ids = set(Job.objects.filter(remote_q).values_list("id", flat=True))
        jobs = [j for j in jobs if j.id in remote_ids]

        # Skip geo/radius logic entirely when remote mode is on

    elif radius and lat and lng:
        try:
            # Parse numeric inputs
            radius_f = float(radius)
            lat_f = float(lat)
            lng_f = float(lng)

            # Prefiltering with previous haversine formula (basic radius) to save API calls
            buffer_radius = radius_f * 1.5
            candidates = []
            for job in jobs:
                if job.latitude is None or job.longitude is None:
                    continue
                try:
                    approx = haversine(lng_f, lat_f, float(job.longitude), float(job.latitude))
                except Exception:
                    continue
                if approx <= buffer_radius:
                    candidates.append(job)

            # Batch road distance/time for remaining (Google Distance Matrix)
            dests = [(j.latitude, j.longitude, j.pk) for j in candidates]
            dm_map = batch_road_distance_and_time(
                lat_f, lng_f, dests, use_traffic=True, traffic_model="best_guess"
            )

            # Keep only jobs within the requested road radius; attach values for UI
            filtered = []
            for job in candidates:
                dm = dm_map.get(job.pk)
                if not dm:
                    continue
                road_miles = dm.get("distance_miles")
                if road_miles is None or road_miles > radius_f:
                    continue

                minutes = dm.get("duration_in_traffic_minutes") or dm.get("duration_minutes")
                job.road_miles = round(road_miles, 1)
                job.drive_minutes = round(minutes) if minutes is not None else None
                filtered.append(job)

            # Sort by road distance, then by drive minutes
            filtered.sort(key=lambda x: (
                getattr(x, "road_miles", 1e9),
                getattr(x, "drive_minutes", 1e9) if getattr(x, "drive_minutes", None) is not None else 1e9,
            ))

            jobs = filtered

        except ValueError:
            # if bad inputs, skip commute filtering entirely
            pass

    # Markers for map
    job_markers = []
    for job in jobs:
        if job.latitude and job.longitude:
            marker = {
                "id": job.id,
                "lat": float(job.latitude),
                "lng": float(job.longitude),
                "title": job.title,
                "company": job.company,
                "location": job.location,
            }
            # optionally include road distance/time for future info windows
            if hasattr(job, "road_miles"):
                marker["road_miles"] = job.road_miles
            if hasattr(job, "drive_minutes") and job.drive_minutes is not None:
                marker["drive_minutes"] = job.drive_minutes
            job_markers.append(marker)

    job_markers_json = json.dumps(job_markers, cls=DjangoJSONEncoder)

    # Count user's applications if logged in
    user_application_count = 0
    if request.user.is_authenticated:
        from applications.models import Application
        user_application_count = Application.objects.filter(user=request.user).count()
    
    return render(request, "jobs/index.html", {
        "jobs": jobs,
        "all_skills": all_skills,
        "selected_skills": skills_filter,
        "job_markers_json": job_markers_json,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
        "user_application_count": user_application_count,
    })

# Now just added ability to view distance/time to job based on actual roadtime not basic radius
def jobs_by_commute_radius(request):
    user_lat = float(request.GET.get("lat"))
    user_lng = float(request.GET.get("lng"))
    radius_miles = float(request.GET.get("radius_miles", 25))

    # prefiltering with previous haversine formula (basic radius)
    buffer_radius = radius_miles * 1.5
    pre = []
    for job in Job.objects.all():
        if job.latitude is None or job.longitude is None:
            continue
        approx = haversine(user_lng, user_lat, job.longitude, job.latitude)
        if approx <= buffer_radius:
            pre.append(job)

    # batch road distance/time for remaining
    dests = [(j.latitude, j.longitude, j.pk) for j in pre]
    dm_map = batch_road_distance_and_time(user_lat, user_lng, dests, use_traffic=True, traffic_model="best_guess")

    # filter by road distance
    results = []
    for job in pre:
        dm = dm_map.get(job.pk)
        if not dm:
            continue
        road_miles = dm["distance_miles"]
        if road_miles is not None and road_miles <= radius_miles:
            job.road_miles = round(road_miles, 1)
            minutes = dm["duration_in_traffic_minutes"] or dm["duration_minutes"]
            job.drive_minutes = round(minutes) if minutes is not None else None
            results.append(job)

    # Sort by road distance, then minutes
    results.sort(key=lambda x: (
        getattr(x, "_road_miles", 1e9),
        getattr(x, "_drive_minutes", 1e9) if getattr(x, "_drive_minutes", None) is not None else 1e9,
    ))

    return render(request, "jobs/index.html", {"jobs": results, "user_lat": user_lat, "user_lng": user_lng, "radius_miles": radius_miles})

def show(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, "jobs/job.html", {
        "job": job,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })

def recruiter_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, "recruiterprofile"):
            messages.error(request, "You must be a recruiter to access this page.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return _wrapped_view



# Recruiter: see their own jobs
@recruiter_required
@login_required
def my_jobs(request):
    if hasattr(request.user, "recruiterprofile"):
        recruiter = request.user.recruiterprofile  # ✅ get the RecruiterProfile
        jobs = Job.objects.filter(recruiter=recruiter)
    else:
        jobs = Job.objects.none()  # or redirect if not a recruiter
    return render(request, "jobs/my_jobs.html", {"jobs": jobs})

@recruiter_required
@login_required
def create_job(request):
    recruiter_profile = getattr(request.user, "recruiterprofile", None)
    if not recruiter_profile:
        messages.error(request, "Only recruiters can post jobs.")
        return redirect('jobs:my_jobs')

    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = recruiter_profile

            print("RecruiterProfile assigned:", recruiter_profile)
            print("RecruiterProfile ID:", recruiter_profile.id)
            print("RecruiterProfile exists in DB:", recruiter_profile.__class__.objects.filter(id=recruiter_profile.id).exists())

            job.save()
            form.save_m2m()
            messages.success(request, "Job posted successfully!")
            return redirect('jobs:my_jobs')
        else:
            messages.error(request, f"Please fix the errors below: {form.errors}")
    else:
        form = JobForm()

    return render(request, 'jobs/create_job.html', {'form': form})

@recruiter_required
@login_required
def edit_job(request, job_id):
    # Get the logged-in user's recruiter profile
    recruiter_profile = getattr(request.user, "recruiterprofile", None)
    if not recruiter_profile:
        messages.error(request, "Only recruiters can edit jobs.")
        return redirect("jobs:my_jobs")

    # Ensure this recruiter owns the job being edited
    job = get_object_or_404(Job, id=job_id, recruiter=recruiter_profile)

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully!")
            return redirect("jobs:my_jobs")
    else:
        form = JobForm(instance=job)

    return render(request, "jobs/job_form.html", {"form": form, "job": job})


# Delete job
@recruiter_required
@login_required
def delete_job(request, job_id):
    recruiter_profile = getattr(request.user, "recruiterprofile", None)
    if not recruiter_profile:
        messages.error(request, "Only recruiters can delete jobs.")
        return redirect("jobs:my_jobs")

    job = get_object_or_404(Job, id=job_id, recruiter=recruiter_profile)

    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted successfully!")
        return redirect("jobs:my_jobs")

    return render(request, "jobs/job_confirm_delete.html", {"job": job})