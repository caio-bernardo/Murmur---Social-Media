from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from ninja import PatchDict
from ninja.router import Router
from ninja.errors import HttpError
from ninja_jwt.tokens import RefreshToken

from accounts.schemas import (
    UserPatch,
    UserPrivate,
    UserPublic,
    UserRegisterIn,
    UserRegisterOut,
)
from app.security import TokenBasedAuth

# Create your views here.

router = Router()


@router.get("/me", auth=TokenBasedAuth(), response=UserPrivate)
def get_user_profile(request):
    """
    Get private version of a user's profile.
    """
    return request.auth


@router.patch("/me", auth=TokenBasedAuth(), response=UserPrivate)
def update_user_profile(request, payload: PatchDict[UserPatch]):
    """
    Update user's profile and internal attributes.
    """
    user = get_object_or_404(User.objects.select_related("profile"), username=request.auth.username)
    for field, value in payload.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)
    user.save()
    user.profile.save()
    return user

@router.delete("/me", auth=TokenBasedAuth(), response={204: None})
def delete_user(request):
    """
    Delete a user.
    """
    user = request.auth
    user.delete()
    return 204, None

@router.post("/register", response={201: UserRegisterOut})
def create_user(request, payload: UserRegisterIn):
    """
    Register a new user.
    """
    if User.objects.filter(username__exact=payload.username).exists():
        raise HttpError(409, "An account already exists under this username")

    try:
        new_user = User.objects.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password.get_secret_value(),
            first_name=payload.first_name,
            last_name=payload.last_name
        )
        refresh = RefreshToken.for_user(new_user)
        data = {
                "user": new_user,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
        }
        return 201, UserRegisterOut.model_validate(data)
    except Exception as e:
        raise HttpError(500, f"Failed to create user: {e}")


@router.get("/{username}", response=UserPublic)
def get_public_user(request, username: str):
    """
    See public version of a user's profile.
    """
    try:
        res = get_object_or_404(User.objects.select_related("profile"), username=username)
        return res
    except Exception as e:
        raise HttpError(500, f"Failed to retrieve user: {e}")
