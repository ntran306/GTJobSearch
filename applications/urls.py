from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    path("apply/<int:job_id>/", views.apply_to_job, name="apply_to_job"),
    path("", views.view_applications, name="view_applications"),
]
