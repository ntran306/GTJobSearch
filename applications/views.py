from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from jobs.models import Job
from .models import Application

@login_required
def apply_to_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    application, created = Application.objects.get_or_create(
        user=request.user,
        job=job,
    )
    if created:
        application.status = "applied"
        application.save()

    return redirect("applications:view_applications")

@login_required
def view_applications(request):
    applications = Application.objects.filter(user=request.user)
    return render(request, "applications/view_applications.html", {"applications": applications})
