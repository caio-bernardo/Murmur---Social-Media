from ninja.security.http import HttpBearer
from ninja_jwt.authentication import JWTAuth

class TokenBasedAuth(JWTAuth, HttpBearer):
    pass
