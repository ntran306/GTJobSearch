from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Job, Skill


def index(request):
    search_term = request.GET.get("search")
    pay_type = request.GET.get("pay_type")
    min_salary = request.GET.get("min_salary")
    max_salary = request.GET.get("max_salary")
    location = request.GET.get("location")
    skills_filter = request.GET.getlist('skills')  # Get skills filter

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

    # Filter by skills
    if skills_filter and skills_filter != ['']:
        jobs = jobs.filter(
            Q(required_skills__name__in=skills_filter) | 
            Q(preferred_skills__name__in=skills_filter)
        ).distinct()

    # Get all skills for the dropdown
    all_skills = Skill.objects.all().order_by('name')

    return render(request, "jobs/index.html", {
        "jobs": jobs,
        "all_skills": all_skills,
        "selected_skills": skills_filter
    })


def show(request, id):
    job = get_object_or_404(Job, id=id)
    return render(request, "jobs/job.html", {"job": job})
