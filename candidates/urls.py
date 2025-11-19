from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('search/', views.search_candidates, name='search_candidates'),
    path("recommendations/", views.recommended_candidates, name="recommended_candidates"),
]
