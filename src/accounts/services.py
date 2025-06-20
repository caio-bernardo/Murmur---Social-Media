from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from ninja import File, UploadedFile
from ninja.errors import HttpError
from ninja_jwt.tokens import RefreshToken

from accounts.schemas import UserRegisterOut


class AccountService:
    @staticmethod
    def get_user_profile(request):
        """
        Get private version of a user's profile.
        """
        return request.auth

    @staticmethod
    def update_user_profile(request, payload):
        """
        Update user's profile and internal attributes.
        """
        user = get_object_or_404(User.objects.select_related("profile"), username=request.auth.username)
        for field, value in payload.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        user.save()
        user.profile.save() #type: ignore
        return user

    @staticmethod
    def delete_user(request) -> None:
        """
        Delete a user.
        """
        user = request.auth
        user.delete()
        return None

    @staticmethod
    def create_user(request, payload):
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
                    "access": str(refresh.access_token) #type: ignore
            }
            return UserRegisterOut.model_validate(data)
        except Exception as e:
            raise HttpError(500, f"Failed to create user: {e}")

    @staticmethod
    def get_public_user(request, username):
        """
        See public version of a user's profile.
        """
        try:
            res = get_object_or_404(User.objects.select_related("profile"), username=username)
            return res
        except Exception as e:
            raise HttpError(500, f"Failed to retrieve user: {e}")

    @staticmethod
    def upload_user_photo(request, photo: File[UploadedFile]) -> None:
        """
        Upload a photo for a user's profile.
        """
        user = request.auth
        user.profile.photo = photo
        user.profile.save()
        return None

    @staticmethod
    def delete_user_photo(request) -> None:
        """
        Delete a user's profile photo.
        """
        user = request.auth
        user.profile.photo.delete()
        return None
