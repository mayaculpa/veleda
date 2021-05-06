from django.urls import path
from rest_framework.authtoken import views

from .views import APIUserDetailView

urlpatterns = [
    path(
        "v1/accounts/auth-token/",
        views.obtain_auth_token,
        name="auth-token",
    ),
    path(
        "v1/accounts/users/<uuid:pk>/",
        APIUserDetailView.as_view(),
        name="user-detail",
    ),
]
