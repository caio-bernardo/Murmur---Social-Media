from ninja import File, PatchDict
from ninja.files import UploadedFile
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
    return 204, AccountService.delete_user(request)

@router.post("/me/photo", auth=TokenBasedAuth(), response={205: None})
def upload_user_photo(request, file: File[UploadedFile]):
    """
    Upload a photo for a user's profile.
    """
    return 205, AccountService.upload_user_photo(request, file)

@router.delete("/me/photo", auth=TokenBasedAuth(), response={204: None})
def delete_user_photo(request):
    """
    Delete a user's profile photo.
    """
    return 204, AccountService.delete_user_photo(request)

@router.post("/register", response={201: UserRegisterOut})
def create_user(request, payload: UserRegisterIn):
    """
    Register a new user.
    """
    return 201, AccountService.create_user(request, payload)


@router.get("/{username}", response=UserPublic)
def get_public_user(request, username: str):
    """
    See public version of a user's profile.
    """
    return AccountService.get_public_user(request, username)
