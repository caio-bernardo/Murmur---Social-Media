from django.contrib.auth.models import User
from django.shortcuts import aget_object_or_404
from ninja import File, UploadedFile
from ninja.errors import HttpError
from ninja_jwt.tokens import RefreshToken

from accounts.schemas import UserRegisterOut


class AccountService:
    @staticmethod
    async def get_user_profile(request):
        """
        Get private version of a user's profile.
        """
        return await aget_object_or_404(
            User.objects.select_related("profile"), username=request.auth.username
        )

    @staticmethod
    async def update_user_profile(request, payload):
        """
        Update user's profile and internal attributes.
        """
        user = await aget_object_or_404(
            User.objects.select_related("profile"), username=request.auth.username
        )
        for field, value in payload.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        await user.asave()
        await user.profile.asave()  # type: ignore
        return user

    @staticmethod
    async def delete_user(request) -> None:
        """
        Delete a user.
        """
        user = request.auth
        await user.adelete()
        return None

    @staticmethod
    async def create_user(request, payload):
        """
        Register a new user.
        """
        if await User.objects.filter(username__exact=payload.username).aexists():
            raise HttpError(409, "An account already exists under this username")

        try:
            new_user = await User.objects.acreate_user(
                username=payload.username,
                email=payload.email,
                password=payload.password.get_secret_value(),
                first_name=payload.first_name,
                last_name=payload.last_name,
            )
            refresh = RefreshToken.for_user(new_user)
            data = {
                "user": new_user,
                "refresh": str(refresh),
                "access": str(refresh.access_token),  # type: ignore
            }
            return UserRegisterOut.model_validate(data)
        except Exception as e:
            raise HttpError(500, f"Failed to create user: {e}")

    @staticmethod
    async def get_public_user(request, username):
        """
        See public version of a user's profile.
        """
        try:
            res = await aget_object_or_404(
                User.objects.select_related("profile"), username=username
            )
            return res
        except Exception as e:
            raise HttpError(500, f"Failed to retrieve user: {e}")

    @staticmethod
    async def upload_user_photo(request, photo: File[UploadedFile]) -> None:
        """
        Upload a photo for a user's profile.
        """
        user = await aget_object_or_404(
            User.objects.select_related("profile"), pk=request.auth.pk
        )
        user.profile.photo = photo  # type: ignore
        await user.profile.asave()  # type: ignore
        return None

    @staticmethod
    async def delete_user_photo(request) -> None:
        """
        Delete a user's profile photo.
        """
        user = await aget_object_or_404(
            User.objects.select_related("profile"), pk=request.auth.pk
        )
        user.profile.photo.delete()  # type: ignore
        return None
