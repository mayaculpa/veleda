from django.urls import path
import oauth2_provider.views as oauth2_views
from django.contrib.auth.decorators import user_passes_test


def is_super(user):
    return user.is_superuser and user.is_active


urlpatterns = [
    path("authorize/", oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path("token/", oauth2_views.TokenView.as_view(), name="token"),
    path("revoke-token/", oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
    # the above are public but we restrict the following:
    path(
        "applications/",
        user_passes_test(is_super)(oauth2_views.ApplicationList.as_view()),
        name="list",
    ),
    path(
        "applications/register/",
        user_passes_test(is_super)(oauth2_views.ApplicationRegistration.as_view()),
        name="register",
    ),
    path("applications/<pk>/", oauth2_views.ApplicationDetail.as_view(), name="detail"),
    path(
        "applications/<pk>/delete/",
        user_passes_test(is_super)(oauth2_views.ApplicationDelete.as_view()),
        name="delete",
    ),
    path(
        "applications/<pk>/update/",
        user_passes_test(is_super)(oauth2_views.ApplicationUpdate.as_view()),
        name="update",
    ),
]
