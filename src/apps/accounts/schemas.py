from django.contrib.auth import get_user_model
from ninja import Field, ModelSchema
from ninja.schema import Schema
from pydantic import EmailStr, field_validator
from pydantic.types import SecretStr

from accounts.models import Profile

User = get_user_model()
#  Registration


class UserRegisterIn(Schema):
    username: str = Field(..., description="User unique indetifier name")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=24,
        description="User's password. Must be at least 8 characters long.",
    )
    password_confirm: SecretStr

    @field_validator("password_confirm", mode="after")
    @classmethod
    def password_match(cls, v, values, **kwargs):
        if "password" in values.data and v != values.data["password"]:
            raise ValueError("Passwords don't match.")
        return v


class ProfilePublic(ModelSchema):
    class Meta:
        model = Profile
        fields = [
            "bio",
            "photo",
            "created_at",
        ]


class ProfilePrivate(ModelSchema):
    class Meta:
        model = Profile
        exclude = ["id", "user"]


class UserPrivate(ModelSchema):
    profile: ProfilePrivate

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
        ]


class UserPublic(ModelSchema):
    profile: ProfilePublic

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]


class UserRegisterOut(Schema):
    user: UserPrivate
    access: str
    refresh: str


class ProfilePatch(ModelSchema):
    class Meta:
        model = Profile
        fields = ["bio"]
        fields_optional = ["__all__"]


class UserPatch(ModelSchema):
    profile: ProfilePatch

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        fields_optional = ["__all__"]
