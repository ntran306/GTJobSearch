# accounts/urls.py
from django.urls import path
from communication.views import contact_user as contact_user_view
from . import views

app_name = "accounts"

urlpatterns = [
    path("signup-choice/", views.signup_choice, name="signup_choice"),
    path("signup/jobseeker/", views.jobseeker_signup, name="jobseeker_signup"),
    path("signup/recruiter/", views.recruiter_signup, name="recruiter_signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("edit/", views.edit_profile, name="edit_profile"),
    path("edit/recruiter/", views.edit_recruiter_profile, name="edit_recruiter_profile"),
    path("view/<int:user_id>/", views.view_profile, name="view_profile"),
    path("view/<int:user_id>/contact/", contact_user_view, name="contact_user"),  # <-- use communication view
    path("connect/", views.connect, name="connect"),
]
