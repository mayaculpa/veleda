from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from oauth2_provider.views.generic import ScopedProtectedResourceView


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

