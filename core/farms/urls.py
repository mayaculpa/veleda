from django.urls import path

from .views import (
    APICoordinatorPingView,
    APICoordinatorListCreateView,
    APICoordinatorDetailView,
    APIControllerPingView,
    APIControllerDetailView,
    APIMqttMessageListView,
    APISiteDetailView,
    APISiteListCreateView,
    CoordinatorSetupSelectView,
    CoordinatorSetupRegisterView,
    SiteSetupView,
    SiteListView,
)

app_name = 'farms'

urlpatterns = [
    path("sites/", SiteListView.as_view(), name="site-list"),
    path("site-setup/", SiteSetupView.as_view(), name="site-setup",),
    path(
        "coordinator-setup/",
        CoordinatorSetupSelectView.as_view(),
        name="coordinator-setup-select",
    ),
    path(
        "coordinator-setup/<uuid:pk>/",
        CoordinatorSetupRegisterView.as_view(),
        name="coordinator-setup-register",
    )
]
