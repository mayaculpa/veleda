from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from oauth2_provider.views.generic import ScopedProtectedResourceView
from rest_framework.authentication import TokenAuthentication


def index(request):
    return render(request, "homepage.html")


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
        else:
            return JsonResponse({"error": "Unknown user"})


class TokenLoginRequiredMixin(AccessMixin):

    """A login required mixin that allows token authentication."""

    def dispatch(self, request, *args, **kwargs):
        """If token was provided, ignore authenticated status."""
        http_auth = request.META.get("HTTP_AUTHORIZATION")

        if http_auth and "Token" in http_auth:
            pass

        elif not request.user.is_authenticated:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class TokenGraphQLView(TokenLoginRequiredMixin, GraphQLView):
    authentication_classes = [TokenAuthentication]


class SessionGraphQLView(LoginRequiredMixin, GraphQLView):
    pass
