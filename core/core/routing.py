from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from farms.consumers import ControllerConsumer
from farms.utils import TokenAuthMiddleware

application = ProtocolTypeRouter(
    {
        "websocket": TokenAuthMiddleware(
            URLRouter(
                [
                    path(
                        "ws-api/v1/farms/controllers/",
                        ControllerConsumer,
                        name="ws-controller",
                    )
                ]
            )
        )
    }
)
