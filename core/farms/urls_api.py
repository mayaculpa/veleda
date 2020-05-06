from django.urls import path

from . import views_api as views

# fmt: off
urlpatterns = [
    path(
        "v1/farms/sites/",
        views.APISiteListCreateView.as_view(),
        name="site-list",
    ),
    path(
        "v1/farms/sites/<uuid:pk>/",
        views.APISiteDetailView.as_view(),
        name="site-detail",
    ),
    path(
        "v1/farms/coordinators/ping/",
        views.APICoordinatorPingView.as_view(),
        name="coordiantor-ping",
    ),
    path(
        "v1/farms/coordinators/",
        views.APICoordinatorListCreateView.as_view(),
        name="coordinator-list",
    ),
    path(
        "v1/farms/coordinators/<uuid:pk>/",
        views.APICoordinatorDetailView.as_view(),
        name="coordinator-detail",
    ),
    path(
        "v1/farms/controllers/ping/",
        views.APIControllerPingView.as_view(),
        name="controller-ping",
    ),
    path(
        "v1/farms/controllers/<uuid:pk>/",
        views.APIControllerDetailView.as_view(),
        name="controller-detail",
    ),
    path(
        "v1/farms/coordinators/<uuid:pk>/mqtt-messages/",
        views.APIMqttMessageListView.as_view(),
        name="mqttmessage-list",
    ),
    path(
        "v1/farms/coordinators/<uuid:pk>/mqtt-messages/<str:created_at>/",
        views.APIMqttMessageDetailView.as_view(),
        name="mqttmessage-detail",
    ),
]
# fmt: on
