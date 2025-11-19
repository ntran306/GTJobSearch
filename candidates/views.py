# candidates/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from accounts.models import JobSeekerProfile, RecruiterProfile  
from jobs.models import Skill
from django.contrib.auth.decorators import login_required
from jobs.models import Job

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

    recommended = None
    selected_job = None
    recruiter_jobs = None

    # Only recruiters can see recommended candidates
        # Only recruiters can see recommended candidates
    if hasattr(request.user, "recruiterprofile"):
        recruiter = request.user.recruiterprofile
        recruiter_jobs = Job.objects.filter(recruiter=recruiter)

        # Job selected from dropdown
        selected_job_id = request.GET.get("recommended_job")
        if selected_job_id:
            selected_job = Job.objects.filter(
                id=selected_job_id, recruiter=recruiter
            ).first()

            if selected_job:
                # 🔹 Use required_skills + preferred_skills instead of job.skills
                required_qs = selected_job.required_skills.all()
                preferred_qs = selected_job.preferred_skills.all()
                job_skills = (required_qs | preferred_qs).distinct()

                # 🔹 Match JobSeekerProfile.skills (M2M to jobs.Skill)
                recommended = (
                    JobSeekerProfile.objects
                    .filter(privacy__in=['public', 'employers_only'])
                    .filter(skills__in=job_skills)
                    .select_related('user')
                    .prefetch_related('skills')
                    .distinct()
                )



    return render(request, 'candidates/search.html', {
        'candidates': candidates,
        'skill_query': skill_query,
        'location_query': location_query,
        'project_query': project_query,
        'skills': skills,
        "recruiter_jobs": recruiter_jobs,
        "selected_job": selected_job,
        "recommended": recommended,
    })



@login_required
def recommended_candidates(request):
    recruiter = getattr(request.user, "recruiterprofile", None)
    if not recruiter:
        return render(request, "candidates/not_recruiter.html")

    # List of jobs posted by this recruiter
    jobs = Job.objects.filter(recruiter=recruiter)

    # Get selected job ID from dropdown
    selected_job_id = request.GET.get("job")

    selected_job = None
    recommended = None

    if selected_job_id:
        selected_job = get_object_or_404(Job, id=selected_job_id, recruiter=recruiter)

        job_skills = selected_job.skills.all()

        recommended = (
            JobSeekerProfile.objects
            .filter(skills__in=job_skills)
            .distinct()
            .annotate(matches=Count('skills'))
            .order_by('-matches')
        )

    return render(request, "candidates/recommended_candidates.html", {
        "jobs": jobs,
        "selected_job": selected_job,
        "recommended": recommended,
    })