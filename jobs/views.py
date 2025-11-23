from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
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
from applications.models import Application
from accounts.models import JobSeekerProfile

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

    recommended = None

    # Show recommended candidates only if recruiter owns the job
    if hasattr(request.user, "recruiterprofile") and job.recruiter == request.user.recruiterprofile:

        # Combine required + preferred skills
        job_skills = list(job.required_skills.all()) + list(job.preferred_skills.all())

        recommended = (
            JobSeekerProfile.objects
            .filter(skills__in=job_skills)
            .distinct()
        )

    return render(request, "jobs/job.html", {
        "job": job,
        "recommended": recommended,
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
    """Create a new job posting with required and preferred skills."""
    # ✅ Get recruiter profile
    if hasattr(request.user, "recruiterprofile"):
        profile = request.user.recruiterprofile
    else:
        messages.error(request, "Only recruiters can create job postings.")
        return redirect("home:index")

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = profile
            job.save()

            # ✅ Handle skills from hidden inputs
            required_ids = request.POST.get("required_skills", "").split(",")
            preferred_ids = request.POST.get("preferred_skills", "").split(",")

            valid_required = Skill.objects.filter(id__in=[s for s in required_ids if s.isdigit()])
            valid_preferred = Skill.objects.filter(id__in=[s for s in preferred_ids if s.isdigit()])

            job.required_skills.set(valid_required)
            job.preferred_skills.set(valid_preferred)
            job.save()

            messages.success(request, "Job created successfully!")
            return redirect("jobs:my_jobs")
        else:
            # 👇 Add this debug print to your terminal
            print("❌ FORM INVALID:", form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobForm()

    skills = list(Skill.objects.values("id", "name"))
    return render(request, "jobs/create_job.html", {
        "form": form,
        "skills": skills,
    })

@login_required
@recruiter_required
def edit_job(request, job_id):
    """Edit an existing job posting with required and preferred skills."""
    if hasattr(request.user, "recruiterprofile"):
        profile = request.user.recruiterprofile
    else:
        messages.error(request, "Only recruiters can edit job postings.")
        return redirect("home:index")

    job = get_object_or_404(Job, id=job_id, recruiter=profile)

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            # ✅ Save job first (excluding skills)
            job = form.save(commit=False)
            job.recruiter = profile
            job.save()

            # ✅ Parse skill IDs safely
            required_ids = [
                s for s in request.POST.get("required_skills", "").split(",") if s.isdigit()
            ]
            preferred_ids = [
                s for s in request.POST.get("preferred_skills", "").split(",") if s.isdigit()
            ]

            valid_required = Skill.objects.filter(id__in=required_ids)
            valid_preferred = Skill.objects.filter(id__in=preferred_ids)

            # ✅ Update ManyToMany fields
            job.required_skills.set(valid_required)
            job.preferred_skills.set(valid_preferred)
            job.save()

            messages.success(request, "Job updated successfully!")
            return redirect("jobs:my_jobs")
        else:
            print("❌ FORM INVALID:", form.errors)
    else:
        form = JobForm(instance=job)

    # ✅ Pass skills data for JS
    skills = list(Skill.objects.values("id", "name"))
    required_skills = list(job.required_skills.values("id", "name"))
    preferred_skills = list(job.preferred_skills.values("id", "name"))

    return render(request, "jobs/edit_job.html", {
        "form": form,
        "skills": skills,
        "job": job,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
    })


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

@recruiter_required
@login_required
def view_applicants(request, job_id):
    job = get_object_or_404(Job, id=job_id, recruiter=request.user.recruiterprofile)
    applicants = job.applications.select_related('user', 'user__jobseekerprofile')  # Changed here
    
    # Count applications by status
    status_counts = {
        'applied': applicants.filter(status='applied').count(),
        'review': applicants.filter(status='review').count(),
        'interview': applicants.filter(status='interview').count(),
        'offer': applicants.filter(status='offer').count(),
        'closed': applicants.filter(status='closed').count(),
    }
    
    # Create user markers data for map
    user_markers = []
    
    for application in applicants:
        user = application.user
        
        # Use jobseekerprofile instead of profile
        if hasattr(user, 'jobseekerprofile'):
            profile = user.jobseekerprofile
            
            # Build location text from available fields
            location_text = profile.location or profile.full_address or ''
            
            # Get coordinates
            lat = float(profile.latitude) if profile.latitude else None
            lng = float(profile.longitude) if profile.longitude else None
            
            marker_data = {
                'id': user.id,
                'name': user.get_full_name() or user.username,
                'role': 'Job Seeker',
                'headline': profile.headline or '',
                'location_text': location_text,
                'lat': lat,
                'lng': lng,
                'profileUrl': reverse('profiles:view_profile', kwargs={'user_id': user.id}),
                'contactUrl': f'/messages/compose/{user.id}/',
            }
            
            # Add marker if we have location data
            if location_text or (lat and lng):
                user_markers.append(marker_data)
    
    return render(request, 'jobs/applicants_list.html', {
        'job': job,
        'applicants': applicants,
        'status_counts': status_counts,
        'user_markers_json': json.dumps(user_markers, cls=DjangoJSONEncoder),
        'MAPS_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    })