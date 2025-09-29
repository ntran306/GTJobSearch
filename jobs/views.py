from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.conf import settings
from .models import Job, Skill
from .utils import haversine
from django.core.serializers.json import DjangoJSONEncoder
import json

def index(request):
    pay_type = request.GET.get("pay_type")
    min_salary = request.GET.get("min_salary")
    max_salary = request.GET.get("max_salary")
    skills_filter = request.GET.getlist('skills')  # Get skills filter

    jobs = Job.objects.all()

    # name and company filter
    search = request.GET.get("search")
    if search:
        jobs = jobs.filter(Q(name__icontains=search) | Q(company__icontains=search))

    # pay type filter
    pay_type = request.GET.get("pay_type")
    if pay_type and pay_type != "all":
        jobs = jobs.filter(pay_type=pay_type)

    # salary filter
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

    # Filter by skills
    if skills_filter and skills_filter != ['']:
        jobs = jobs.filter(
            Q(required_skills__name__in=skills_filter) | 
            Q(preferred_skills__name__in=skills_filter)
        ).distinct()

    # Get all skills for the dropdown
    all_skills = Skill.objects.all().order_by('name')

    # radius and location filter
    radius = request.GET.get("radius")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    lat_f = lng_f = radius_f = None
    if radius and lat and lng:
        try:
            radius_f = float(radius)
            lat_f = float(lat)
            lng_f = float(lng)
            jobs = jobs.filter_within_radius(lat_f, lng_f, radius_f)

            # calculate distance for each job
            for job in jobs:
                if job.latitude and job.longitude:
                    try:
                        job.distance = round(
                            haversine(lng_f, lat_f, float(job.longitude), float(job.latitude)), 1
                        )
                    except Exception:
                        job.distance = None
        except ValueError:
            pass

    # markers for map
    job_markers = []
    for job in jobs:
        if job.latitude and job.longitude:
            marker = {
                "id": job.id,
                "lat": float(job.latitude),
                "lng": float(job.longitude),
                "title": job.name,
                "company": job.company,
                "location": job.location,
            }
            if hasattr(job, "distance"):
                marker["distance"] = job.distance
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
        "user_application_count": user_application_count,  # Add this
    })

    return render(request, "jobs/index.html", {
        "jobs": jobs,
        "all_skills": all_skills,
        "selected_skills": skills_filter,
        "job_markers_json": job_markers_json,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })

def show(request, id):
    job = get_object_or_404(Job, id=id)
    return render(request, "jobs/job.html", {
        "job": job,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })
