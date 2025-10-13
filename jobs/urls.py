from django.urls import path
from . import views

app_name = 'jobs'  # important for namespacing in templates

urlpatterns = [
    # Recruiter: see their own jobs
    path("my-jobs/", views.my_jobs, name="my_jobs"),

    # Job creation/edit/deletion (recruiters only)
    path("create/", views.create_job, name="create_job"),
    path("<int:job_id>/edit/", views.edit_job, name="edit_job"),
    path("<int:job_id>/delete/", views.delete_job, name="delete_job"),

    # Job seeker: view a single job
    path("<int:job_id>/", views.show, name="show"),

    # Job seeker: list and search jobs
    path("", views.index, name="index"),
]

