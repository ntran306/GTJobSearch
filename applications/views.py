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
    note = request.POST.get("note", "")  # grab the note from the form
    application, created = Application.objects.get_or_create(
        user=request.user,
        job=job,
    )

    # Always ensure it has a valid status
    if created or not application.status:
        application.status = "applied"
        if note:
            application.note = note
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
    # Get the application
    application = get_object_or_404(Application, id=application_id)
    
    # Only allow the recruiter who posted the job to update status
    is_recruiter = (
        hasattr(request.user, 'recruiterprofile') and 
        application.job.recruiter == request.user.recruiterprofile
    )
    
    if not is_recruiter:
        messages.error(request, "Only the recruiter who posted this job can update application status.")
        return redirect('jobs:index')

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Application.STATUS_CHOICES).keys():
            application.status = new_status
            application.save()
            messages.success(request, f"Application status updated to {application.get_status_display()}.")
            # Redirect back to the applicants list for this job
            return redirect('jobs:view_applicants', job_id=application.job.id)
        else:
            messages.error(request, "Invalid status selected.")
            return redirect('applications:update_status', application_id=application_id)

    return render(request, "applications/update_status.html", {"application": application})
