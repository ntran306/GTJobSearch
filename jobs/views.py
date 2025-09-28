from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.conf import settings
from .models import Job
from .utils import haversine
from django.core.serializers.json import DjangoJSONEncoder
import math, json

def index(request):
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

    return render(request, "jobs/index.html", {
        "jobs": jobs,
        "job_markers_json": job_markers_json,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })

def show(request, id):
    job = get_object_or_404(Job, id=id)
    return render(request, "jobs/job.html", {
        "job": job,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })
