from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from jobs.models import Job
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
    applications = Application.objects.filter(user=request.user)
    return render(request, "applications/view_applications.html", {"applications": applications})

@login_required
def update_application_status(request, application_id):
    application = get_object_or_404(Application, id=application_id, user=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Application.STATUS_CHOICES).keys():
            application.status = new_status
            application.save()
        else:
            return HttpResponseForbidden("Invalid status")
        
        return redirect("applications:view_applications")

    return render(request, "applications/update_status.html", {"application": application})
