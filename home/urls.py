# home/urls.py
from django.urls import path
from . import views

app_name = 'home'  # This namespaces your URLs

urlpatterns = [
    path("", views.index, name="index"),      # homepage
    path("about/", views.about, name="about"), # about page
]
