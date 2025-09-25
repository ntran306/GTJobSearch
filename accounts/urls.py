from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Original ones
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),

    # Extended ones
    path("signup/choice/", views.signup_choice, name="signup_choice"),
    path("signup/jobseeker/", views.jobseeker_signup, name="jobseeker_signup"),
    path("signup/recruiter/", views.recruiter_signup, name="recruiter_signup"),

    path("profile/jobseeker/", views.view_jobseeker_profile, name="view_jobseeker_profile"),
    path("profile/recruiter/", views.view_recruiter_profile, name="view_recruiter_profile"),
]
