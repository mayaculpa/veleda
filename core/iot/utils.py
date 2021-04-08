from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from iot.models import ControllerComponent


class TokenAuthMiddleware:
    """
    A token auth middleware for controllers
    """

    controller_ws_path = "ws-api/v1/farms/controllers/"

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope["controller"] = await self.get_controller(scope.get("subprotocols"))
        return await self.app(scope, receive, send)

    @staticmethod
    async def get_controller(subprotocols):
        """
        Extract the token and return the corresponding controller

        During the WebSocket connection the subprotocols can be set. These are
        separated by ", ". As a means of authentication, a token is defined as a
        subprotocol. It is shown below and the token value itself is underlined.

        sec-websocket-protocol: token_abc123, other_sub_protocol
                                    ^~~~~~
        """

        if subprotocols:
            tokens = [
                subprotocol
                for subprotocol in subprotocols
                if subprotocol.startswith("token")
            ]
            if tokens:
                token = tokens[0].split("_")[1]
                try:
                    return await database_sync_to_async(
                        ControllerComponent.objects.get
                    )(auth_token__key=token)
                except ControllerComponent.DoesNotExist:
                    pass
        return None

class PathAuthMiddleware:
    """Map middleware according to path"""

    def __init__(self, app):
        self.controller_app = TokenAuthMiddleware(app)
        self.other_app = AuthMiddlewareStack(app)

    async def __call__(self, scope, receive, send):
        if scope["path"] == f"/{TokenAuthMiddleware.controller_ws_path}":
            return await self.controller_app(scope, receive, send)
        return await self.other_app(scope, receive, send)
