"""
Urls for the account app

Works in tandem with the integrated auth and the django-registration app
"""

from django.urls import path

from .views import APIUserDetailView


urlpatterns = [
    path(
        "v1/accounts/users/<uuid:pk>/",
        APIUserDetailView.as_view(),
        name="user-detail",
    ),
]
