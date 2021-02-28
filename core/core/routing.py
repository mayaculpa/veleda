from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from iot.consumers import ControllerConsumer
from iot.utils import TokenAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": TokenAuthMiddleware(
            URLRouter(
                [
                    path(
                        "ws-api/v1/farms/controllers/",
                        ControllerConsumer.as_asgi(),
                        name="ws-controller",
                    )
                ]
            )
        )
    }
)
