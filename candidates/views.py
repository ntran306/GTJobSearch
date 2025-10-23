# candidates/views.py
from django.shortcuts import render
from django.db.models import Q
from accounts.models import JobSeekerProfile  # <-- your real candidate model
from jobs.models import Skill

# Show all public/visible candidates, filter by skill, location, projects (TextField)
def search_candidates(request):
    skill_query = (request.GET.get('skill') or "").strip()
    location_query = (request.GET.get('location') or "").strip()
    project_query = (request.GET.get('project') or "").strip()

    # Only candidates who are visible to recruiters
    candidates = (
        JobSeekerProfile.objects
        .filter(privacy__in=['public', 'employers_only'])
        .select_related('user')
        .prefetch_related('skills')
        .order_by('user__username')
    )

    if skill_query:
        # Skill is M2M to jobs.Skill(name)
        candidates = candidates.filter(skills__name__icontains=skill_query)

    if location_query:
        candidates = candidates.filter(location__icontains=location_query)

    if project_query:
        # projects is a TextField on JobSeekerProfile per your earlier schema
        candidates = candidates.filter(projects__icontains=project_query)

    # Avoid duplicates if multiple skills match
    candidates = candidates.distinct()

    skills = Skill.objects.all().order_by('name')

    print("DEBUG: Candidates found =", candidates.count())
    for c in candidates:
        print(" -", c.user.username, "| privacy:", c.privacy, "| location:", c.location)

    return render(request, 'candidates/search.html', {
        'candidates': candidates,
        'skill_query': skill_query,
        'location_query': location_query,
        'project_query': project_query,
        'skills': skills,
    })
