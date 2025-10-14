"""
URL configuration for GTJobSearch project.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

def jobseeker_home(request):
    return HttpResponse("<h1>Jobseeker Homepage (placeholder)</h1>")

def recruiter_home(request):
    return HttpResponse("<h1>Recruiter Homepage (placeholder)</h1>")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls")),         # homepage
    path("accounts/", include("accounts.urls")),  # accounts app
    path("jobs/", include("jobs.urls")), # jobs app
    path("jobseeker/home", jobseeker_home, name="jobseeker_home"), #jobseeker home page
    path("recruiter/home", recruiter_home, name="recruiter_home"), #recruiter home page
    path("applications/", include("applications.urls", namespace="applications")), # applications app
    path('candidates/', include('candidates.urls', namespace="candidates")), # candidates app
    path('profiles/', include('profiles.urls', namespace="profiles")), # profiles app
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 