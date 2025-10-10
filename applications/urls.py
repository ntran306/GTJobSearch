from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('', views.view_applications, name='view_applications'),
    path('update/<int:application_id>/', views.update_application_status, name='update_status'),
    path('apply/<int:job_id>/', views.apply_to_job, name='apply_to_job'),
  # <-- Make sure this exists
]

