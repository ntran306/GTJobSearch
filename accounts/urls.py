from django.urls import path
from . import views

app_name = "accounts"   # 👈 this must exist!

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
]
