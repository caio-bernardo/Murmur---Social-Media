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
from murmur.security import AsyncTokenBasedAuth
from accounts.services import AccountService

router = Router()


@router.get("/me", auth=AsyncTokenBasedAuth(), response=UserPrivate)
async def get_user_profile(request):
    """
    Get private version of a user's profile.
    """
    return await AccountService.get_user_profile(request)


@router.patch("/me", auth=AsyncTokenBasedAuth(), response=UserPrivate)
async def update_user_profile(request, payload: PatchDict[UserPatch]):
    """
    Update user's profile and internal attributes.
    """
    return await AccountService.update_user_profile(request, payload)


@router.delete("/me", auth=AsyncTokenBasedAuth(), response={204: None})
async def delete_user(request):
    """
    Delete a user.
    """
    return 204, await AccountService.delete_user(request)


@router.post("/me/photo", auth=AsyncTokenBasedAuth(), response={205: None})
async def upload_user_photo(request, file: File[UploadedFile]):
    """
    Upload a photo for a user's profile.
    """
    return 205, await AccountService.upload_user_photo(request, file)


@router.delete("/me/photo", auth=AsyncTokenBasedAuth(), response={204: None})
async def delete_user_photo(request):
    """
    Delete a user's profile photo.
    """
    return 204, await AccountService.delete_user_photo(request)


@router.post("/register", response={201: UserRegisterOut})
async def create_user(request, payload: UserRegisterIn):
    """
    Register a new user.
    """
    return 201, await AccountService.create_user(request, payload)


@router.get("/{username}", response=UserPublic)
async def get_public_user(request, username: str):
    """
    See public version of a user's profile.
    """
    return await AccountService.get_public_user(request, username)
