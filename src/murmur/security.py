from ninja.security.http import HttpBearer
from ninja_jwt.authentication import JWTAuth, AsyncJWTAuth


class TokenBasedAuth(JWTAuth, HttpBearer):
    pass


class AsyncTokenBasedAuth(AsyncJWTAuth, HttpBearer):
    pass
