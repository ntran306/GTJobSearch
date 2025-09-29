from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from jobs.models import Job, Skill
from .models import Application
from django.http import HttpResponseForbidden

@login_required
def apply_to_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    application, created = Application.objects.get_or_create(
        user=request.user,
        job=job,
    )

    # Always ensure it has a valid status
    if created or not application.status:
        application.status = "applied"
        application.save()

    return redirect("applications:view_applications")


@login_required
def view_applications(request):
    # Get all applications for this user
    applications = Application.objects.filter(user=request.user).select_related('job')

    recommended_jobs = Job.objects.none()  # Default empty queryset
    user_skills_list = []

    # Check if user has a JobSeekerProfile
    if hasattr(request.user, 'jobseekerprofile'):
        user_skills = request.user.jobseekerprofile.skills.all()
        user_skills_list = list(user_skills.values_list('name', flat=True))
        
        if user_skills.exists():
            applied_job_ids = applications.values_list('job_id', flat=True)
            
            # Find recommended jobs based on skills
            recommended_jobs = Job.objects.filter(
                Q(required_skills__in=user_skills) | Q(preferred_skills__in=user_skills)
            ).exclude(id__in=applied_job_ids).distinct()[:6]

    context = {
        'applications': applications,
        'recommended_jobs': recommended_jobs,
        'user_skills': user_skills_list,
    }

    return render(request, 'applications/view_applications.html', context)



@login_required
def update_application_status(request, application_id):
    application = get_object_or_404(Application, id=application_id, user=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Application.STATUS_CHOICES).keys():
            application.status = new_status
            application.save()
            messages.success(request, "Application status updated successfully.")
        else:
            return HttpResponseForbidden("Invalid status")
        
        return redirect("applications:view_applications")

    return render(request, "applications/update_status.html", {"application": application})
