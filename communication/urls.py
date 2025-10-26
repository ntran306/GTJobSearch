from django.urls import path
from . import views

app_name = "communication"

urlpatterns = [
    path("contact/<int:user_id>/", views.contact_user, name="contact_user"),
]