"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.views.generic.base import RedirectView

from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views as root_views
from . import oauth2_views


urlpatterns = [
    path("", root_views.index, name="index"),
    path("admin/", admin.site.urls, name="admin"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("accounts/", include("django_registration.backends.activation.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    # OAuth2 Endpoints
    path(
        "o/",
        include(
            (oauth2_views.urlpatterns, "oauth2_provider"), namespace="oauth2_provider"
        ),
    ),
    path("api/v1/userinfo/", root_views.UserInfo.as_view(), name="api-v1-userinfo"),
    # Static files
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("img/favicon.ico")),
        name="favicon",
    ),
]

urlpatterns += staticfiles_urlpatterns()
