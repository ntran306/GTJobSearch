from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Original ones
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path('logout/', views.logout_view, name='logout'),


    # Sign Up
    path("signup/choice/", views.signup_choice, name="signup_choice"),
    path("signup/jobseeker/", views.jobseeker_signup, name="jobseeker_signup"),
    path("signup/recruiter/", views.recruiter_signup, name="recruiter_signup"),

    # Universal profile
    path("profile/", views.profile_view, name="profile"),
]

