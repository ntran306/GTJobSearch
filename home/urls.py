from django.urls import path
from . import views

app_name = "home"  # so {% url 'home:index' %} works

urlpatterns = [
    path("", views.index, name="index"),
]
