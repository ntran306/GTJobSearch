from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='jobs.index'),
    path('<int:id>/', views.show,name='jobs.show'),
]