from django.shortcuts import render,  get_object_or_404
from .models import Job


def index(request):
    search_term = request.GET.get('search')
    pay_type = request.GET.get('pay_type') # Trying to allow filtering by job name, company name, and pay type
    min_salary = request.GET.get('min_salary')
    max_salary = request.GET.get('max_salary')
    location = request.GET.get('location') # Will try to implement location filtering later, but just checks like name
    skills_filter = request.GET.getlist('skills')  # Get list of skills

    jobs = Job.objects.all()

    # Filter by job/company name
    if search_term:
        jobs = jobs.filter(name__icontains=search_term) | Job.filter(company__icontains=search_term)

    # Filter by pay type & salary range
    if pay_type and pay_type != 'all':
        jobs = jobs.filter(pay_type=pay_type)
    if min_salary:
        jobs = jobs.filter(pay_min__gte=min_salary)
    if max_salary:
        jobs = jobs.filter(pay_max__lte=max_salary)

    # Filter by location (just a simple substring match for now)
    if location:
        jobs = jobs.filter(location__icontains=location)

    if skills_filter:
        for skill in skills_filter:
            jobs = jobs.filter(skills_required__icontains=skill)
    
    template_data = {}
    template_data['title'] = 'Job Listings'
    template_data['jobs'] = jobs
    return render(request, 'jobs/index.html', {'jobs': jobs})

def show(request, id):
    job = Job.objects.get(id=id)
    template_data = {}
    template_data['title'] = job.name
    template_data['job'] = job
    return render(request, 'jobs/job.html', {'job_id': template_data})