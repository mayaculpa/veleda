import rest_framework
from django.http import JsonResponse
from django.shortcuts import render
from graphene_django.views import GraphQLView
from oauth2_provider.views.generic import ScopedProtectedResourceView
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings


def index(request):
    context = {}
    if request.user.is_authenticated:
        try:
            context["token"] = Token.objects.get(user=request.user)
        except Token.DoesNotExist:
            context["token"] = None
    return render(request, "homepage.html", context)


class UserInfo(ScopedProtectedResourceView):
    required_scopes = ["userinfo-v1"]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return JsonResponse(
                {
                    "name": request.user.get_full_name(),
                    "email": request.user.email,
                    "username": request.user.username,
                }
            )
        return JsonResponse({"error": "Unknown user"})


class DRFAuthenticatedGraphQLView(GraphQLView):
    """Add DRF authentication to classes (session, token, OAuth2) to the GraphQL view."""

    def parse_body(self, request):
        if isinstance(request, rest_framework.request.Request):
            return request.data
        return super().parse_body(request)

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        view = permission_classes((IsAuthenticated,))(view)
        view = authentication_classes(api_settings.DEFAULT_AUTHENTICATION_CLASSES)(view)
        view = api_view(["GET", "POST"])(view)
        return view
