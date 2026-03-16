import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)

@database_sync_to_async
def _get_user(token_str: str):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        token = AccessToken(token_str)
        return User.objects.get(id=token["user_id"])
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])

        if token_list:
            scope["user"] = await _get_user(token_list[0])
        else:
            scope["user"] = AnonymousUser()

        if not scope["user"].is_authenticated:
            logger.warning(
                "WS connection rejected — no valid token. path=%s",
                scope.get("path", "?"),
            )
            await send({"type": "websocket.close", "code": 4401})
            return

        return await super().__call__(scope, receive, send)
