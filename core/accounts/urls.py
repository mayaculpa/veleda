from django.urls import path

from . import views

app_name = "accounts"


urlpatterns = [path("signup/", views.SignUp.as_view(), name="signup")]

