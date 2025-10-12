from django.shortcuts import render
from accounts.models import JobSeekerProfile
from jobs.models import Skill

def search_candidates(request):
    skill_query = request.GET.get('skill', '')
    location_query = request.GET.get('location', '')
    project_query = request.GET.get('project', '')

    # Start with all visible candidates
    candidates = JobSeekerProfile.objects.filter(privacy__in=['public', 'employers_only'])
    skills = Skill.objects.all()

    # Apply filters if user searched
    if skill_query or location_query or project_query:
        if skill_query:
            candidates = candidates.filter(skills__name__icontains=skill_query)
        if location_query:
            candidates = candidates.filter(location__icontains=location_query)
        if project_query:
            candidates = candidates.filter(projects__icontains=project_query)

        return render(request, 'candidates/search_results.html', {
            'candidates': candidates.distinct(),
            'skill_query': skill_query,
            'location_query': location_query,
            'project_query': project_query,
            'skills': skills,
        })

    # If no search input yet, show the search form
    return render(request, 'candidates/search_form.html', {
        'skill_query': skill_query,
        'location_query': location_query,
        'project_query': project_query,
        'skills': skills,
    })
