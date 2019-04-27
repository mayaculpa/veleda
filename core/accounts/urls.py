"""
Urls for the account app

Works in tandem with the integrated auth and the django-registration app
"""

from django.urls import path

from django_registration.backends.activation.views import RegistrationView

from .forms import UserRegistrationForm

app_name = "accounts"


urlpatterns = [
    path(
        "register/",
        RegistrationView.as_view(form_class=UserRegistrationForm),
        name="signup",
    )
]
