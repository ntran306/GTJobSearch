"""
URL configuration for GTJobSearch project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
def jobseeker_home(request):
    return HttpResponse("<h1>Jobseeker Homepage (placeholder)</h1>")

def recruiter_home(request):
    return HttpResponse("<h1>Recruiter Homepage (placeholder)</h1>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    #path('jobs/', include('jobs.urls')),
    path('accounts/', include('accounts.urls')),
    path("jobseeker/home", jobseeker_home, name="jobseeker_home"),
    path("recruiter/home", recruiter_home, name="recruiter_home"),
]
