from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from farms.consumers import CoordinatorConsumer

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    path(
                        "ws-api/v1/farms/coordinators/<uuid:pk>/",
                        CoordinatorConsumer,
                        name="ws-coordinator",
                    )
                ]
            )
        )
    }
)
