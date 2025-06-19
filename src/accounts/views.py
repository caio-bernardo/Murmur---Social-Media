from ninja import PatchDict
from ninja.router import Router

from accounts.schemas import (
    UserPatch,
    UserPrivate,
    UserPublic,
    UserRegisterIn,
    UserRegisterOut,
)
from app.security import TokenBasedAuth
from accounts.services import AccountService

router = Router()


@router.get("/me", auth=TokenBasedAuth(), response=UserPrivate)
def get_user_profile(request):
    """
    Get private version of a user's profile.
    """
    return AccountService.get_user_profile(request)


@router.patch("/me", auth=TokenBasedAuth(), response=UserPrivate)
def update_user_profile(request, payload: PatchDict[UserPatch]):
    """
    Update user's profile and internal attributes.
    """
    return AccountService.update_user_profile(request, payload)


@router.delete("/me", auth=TokenBasedAuth(), response={204: None})
def delete_user(request):
    """
    Delete a user.
    """
    return AccountService.delete_user(request)


@router.post("/register", response={201: UserRegisterOut})
def create_user(request, payload: UserRegisterIn):
    """
    Register a new user.
    """
    return AccountService.create_user(request, payload)


@router.get("/{username}", response=UserPublic)
def get_public_user(request, username: str):
    """
    See public version of a user's profile.
    """
    return AccountService.get_public_user(request, username)