"""
URL configuration for GTJobSearch project.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def jobseeker_home(request):
    return HttpResponse("<h1>Jobseeker Homepage (placeholder)</h1>")

def recruiter_home(request):
    return HttpResponse("<h1>Recruiter Homepage (placeholder)</h1>")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls")),         # homepage
    path("accounts/", include("accounts.urls")),  # accounts app
    # path("jobs/", include("jobs.urls")),
    path("jobseeker/home", jobseeker_home, name="jobseeker_home"),
    path("recruiter/home", recruiter_home, name="recruiter_home"),
]
