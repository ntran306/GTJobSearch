from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('candidate-search/', views.candidate_search, name='candidate_search'),
    path('view/<int:user_id>/', views.view_profile, name='view_profile'),  # ✅ add this
]
