import debug_toolbar
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic.base import RedirectView
from rest_framework.authtoken.views import obtain_auth_token

from core import oauth2_views
from core import views as root_views

urlpatterns = [
    path("", root_views.index, name="index"),
    path("admin/", admin.site.urls, name="admin"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("api/", include("accounts.urls_api")),
    path("accounts/", include("django_registration.backends.activation.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    # IoT URLs
    path("iot/", include("iot.urls", namespace="iot")),
    # Greenhouse URLs
    path("greenhouse/", include("greenhouse.urls", namespace="greenhouse")),
    # API Endpoints
    path(
        "graphql/",
        root_views.DRFAuthenticatedGraphQLView.as_view(graphiql=True),
        name="graphql",
    ),
    path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
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
    # Debug Toolbar
    path("__debug__/", include(debug_toolbar.urls)),
]

urlpatterns += staticfiles_urlpatterns()
