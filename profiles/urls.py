from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('recruiter/search/', views.candidate_search, name='candidate_search'),
]
