from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from farms.models import ControllerAuthToken


class TokenAuthMiddleware:
    """
    A token auth middleware for controllers
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return TokenAuthMiddlewareInstance(scope, self)


class TokenAuthMiddlewareInstance:
    """
    Yeah, this is black magic:
    https://github.com/django/channels/issues/1399
    """

    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        """Add controller to scope with the auth token"""
        if subprotocols := self.scope.get("subprotocols"):
            self.scope["controller"] = await self.get_controller(subprotocols)
        else:
            self.scope["controller"] = None
        inner = self.inner(self.scope)
        return await inner(receive, send)

    @staticmethod
    @database_sync_to_async
    def get_controller(subprotocols):
        """
        Extract the token and return the corresponding controller

        During the WebSocket connection the subprotocols can be set. These are
        separated by ", ". As a means of authentication, a token is defined as a
        subprotocol. It is shown below and the token value itself is underlined.

        sec-websocket-protocol: token_abc123, other_sub_protocol
                                    ^~~~~~
        """
        try:
            tokens = list(filter(lambda x: x.startswith("token"), subprotocols))
            if tokens:
                token = tokens[0].split("_")[1]
                return ControllerAuthToken.objects.get(key=token).controller
            return None
        except ControllerAuthToken.DoesNotExist:
            return None


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))
