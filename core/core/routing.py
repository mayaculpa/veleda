from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from iot.consumers import ControllerConsumer
from iot.utils import PathAuthMiddleware, TokenAuthMiddleware
from iot.consumers import MyGraphqlWsConsumer

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": PathAuthMiddleware(
            URLRouter(
                [
                    path(
                        TokenAuthMiddleware.controller_ws_path,
                        ControllerConsumer.as_asgi(),
                        name="ws-controller",
                    ),
                    path(
                        "graphql/",
                        MyGraphqlWsConsumer.as_asgi(),
                        name="graphql-subscription",
                    ),
                ]
            )
        ),
    }
)
