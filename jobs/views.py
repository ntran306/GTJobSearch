from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Job


def index(request):
    search_term = request.GET.get("search")
    pay_type = request.GET.get("pay_type")
    min_salary = request.GET.get("min_salary")
    max_salary = request.GET.get("max_salary")
    location = request.GET.get("location")

    jobs = Job.objects.all()

    # Filter by job/company name
    if search_term:
        jobs = jobs.filter(Q(name__icontains=search_term) | Q(company__icontains=search_term))

    # Filter by pay type & salary range
    if pay_type and pay_type != "all":
        jobs = jobs.filter(pay_type=pay_type)
    if min_salary:
        jobs = jobs.filter(pay_min__gte=min_salary)
    if max_salary:
        jobs = jobs.filter(pay_max__lte=max_salary)

    # Filter by location
    if location:
        jobs = jobs.filter(location__icontains=location)

    return render(request, "jobs/index.html", {"jobs": jobs})


def show(request, id):
    job = get_object_or_404(Job, id=id)
    return render(request, "jobs/jobs.html", {"job": job})
