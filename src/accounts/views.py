from django.contrib.auth.models import User
from ninja import PatchDict
from ninja.router import Router
from ninja.errors import HttpError
from ninja_jwt.tokens import RefreshToken

from accounts.models import Profile
from accounts.schemas import (
    ProfilePrivateSchema,
    UserPatchSchema,
    UserPrivateSchema,
    UserPublicSchema,
    UserRegisterInSchema,
    UserRegisterOutSchema,
)
from app.security import TokenBasedAuth

# Create your views here.

router = Router()

@router.get("/me", auth=TokenBasedAuth, response=UserPrivateSchema)
def get_user_profile(request):
    """
    Get private version of a user's profile.
    """
    try:
        profile = Profile.objects.get(user=request.auth)
    except Exception as e:
        raise HttpError(500, f"Failed to retrieve user: {e}")
    else:
        return UserPrivateSchema(
            profile=ProfilePrivateSchema.model_validate(profile),
            **request.auth
        )

@router.patch("/me", auth=TokenBasedAuth, response=UserPrivateSchema)
def update_user_profile(request, payload: PatchDict[UserPatchSchema]):
    """
    Update user's profile and internal attributes.
    """
    pass

@router.delete("/me", auth=TokenBasedAuth)
def delete_user(request):
    """
    Delete a user.
    """
    pass

@router.get("/{username}", response=UserPublicSchema)
async def get_public_user(request, username: str):
    """
    See public version of a user's profile.
    """
    try:
        return await User.objects.aget(username=username)
    except Exception as e:
        raise HttpError(500, f"Failed to retrieve user: {e}")

@router.post("/register", response=UserRegisterOutSchema)
def create_user(request, payload: UserRegisterInSchema):
    """
    Register a new user.
    """
    if User.objects.filter(email__iexact=payload.email).exists():
        raise HttpError(409, "An account already exists under this email")

    try:
        new_user = User.objects.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password.get_secret_value(),
            first_name=payload.first_name,
            last_name=payload.last_name
        )
        refresh = RefreshToken.for_user(new_user)
        return UserRegisterOutSchema.model_validate(refresh)
    except Exception as e:
        raise HttpError(500, f"Failed to create user: {e}")
