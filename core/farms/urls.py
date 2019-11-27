from django.urls import path

from .views import CoordinatorSetupView, CoordinatorPingView, CoordinatorDetailView, FarmDetailView

urlpatterns = [
    path(
        "setup/",
        CoordinatorSetupView.as_view(),
        name="coordinator_setup"
    ),
    path(
        "api/v1/farms/coordinators/ping/",
        CoordinatorPingView.as_view(),
        name="coordiantor_ping",
    ),
    path(
        "api/v1/farms/coordinators/<uuid:pk>/",
        CoordinatorDetailView.as_view(),
        name="coordinator-detail",
    ),
    path("api/v1/farms/<uuid:pk>/", FarmDetailView.as_view(), name="farm-detail",),
]
