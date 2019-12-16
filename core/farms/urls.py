from django.urls import path

from .views import (
    CoordinatorSetupSelectView,
    CoordinatorSetupRegisterView,
    CoordinatorPingView,
    CoordinatorDetailView,
    ControllerPingView,
    ControllerDetailView,
    FarmDetailView,
    FarmSetupView,
    FarmListView,
)

urlpatterns = [
    path("farms/", FarmListView.as_view(), name="farm-list"),
    path("farm-setup/", FarmSetupView.as_view(), name="farm-setup",),
    path(
        "coordinator-setup/",
        CoordinatorSetupSelectView.as_view(),
        name="coordinator-setup-select",
    ),
    path(
        "coordinator-setup/<uuid:pk>/",
        CoordinatorSetupRegisterView.as_view(),
        name="coordinator-setup-register",
    ),
    path(
        "api/v1/farms/coordinators/ping/",
        CoordinatorPingView.as_view(),
        name="coordiantor-ping",
    ),
    path(
        "api/v1/farms/coordinators/<uuid:pk>/",
        CoordinatorDetailView.as_view(),
        name="coordinator-detail",
    ),
    path(
        "api/v1/farms/controller/ping/",
        ControllerPingView.as_view(),
        name="controller-ping",
    ),
    path(
        "api/v1/farms/controller/<uuid:pk>/",
        ControllerDetailView.as_view(),
        name="controller-detail",
    ),
    path("api/v1/farms/<uuid:pk>/", FarmDetailView.as_view(), name="farm-detail",),
]
