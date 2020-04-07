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
)

urlpatterns = [
    path("v1/farms/sites/", APISiteListCreateView.as_view(), name="site-list",),
    path("v1/farms/sites/<uuid:pk>/", APISiteDetailView.as_view(), name="site-detail",),
    path(
        "v1/farms/coordinators/ping/",
        APICoordinatorPingView.as_view(),
        name="coordiantor-ping",
    ),
    path(
        "v1/farms/coordinators/", APICoordinatorListCreateView.as_view(), name="coordinators",
    ),
    path(
        "v1/farms/coordinators/<uuid:pk>/",
        APICoordinatorDetailView.as_view(),
        name="coordinator-detail",
    ),
    path(
        "v1/farms/controllers/ping/", APIControllerPingView.as_view(), name="controller-ping",
    ),
    path(
        "v1/farms/controllers/<uuid:pk>/",
        APIControllerDetailView.as_view(),
        name="controller-detail",
    ),
    path(
        "v1/farms/coordinators/<uuid:pk>/mqtt/",
        APIMqttMessageListView.as_view(),
        name="coordinator-mqtt",
    ),
]
