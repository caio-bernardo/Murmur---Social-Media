from django.contrib.auth import get_user_model
from ninja import Field
from ninja.schema import Schema
from ninja_jwt.schema import TokenRefreshOutputSchema
from pydantic import EmailStr, validator
from pydantic.types import SecretStr

from accounts.models import Profile

User = get_user_model()
#  Registration

class UserRegisterInSchema(Schema):
    username: str = Field(..., description="User unique indetifier name")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    password: SecretStr = Field(..., min_length=8, max_length=24, description="User's password. Must be at least 8 characters long.")
    password_confirm: SecretStr

    @validator("password_confirm")
    def password_match(cls, v, values, **kwargs):
        if 'password' in values and v != values["password"]:
            raise ValueError("Passwords don't match.")
        return v

class UserRegisterOutSchema(Schema):
    token: TokenRefreshOutputSchema

# Access

class ProfilePublicSchema(Schema):
    class Meta:
        model = Profile
        fields = ["bio", "created_at"]

class ProfilePrivateSchema(Schema):
    class Meta:
        model=Profile
        fields = ["bio", "created_at", "updated_at"]

class UserPublicSchema(Schema):
    profile: ProfilePublicSchema
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]

class UserPrivateSchema(Schema):
    profile: ProfilePrivateSchema
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

# Update
class ProfilePathSchema(Schema):
    class Meta:
        model = Profile
        fields = ["bio"]
        fields_optional = "__all__"

class UserPatchSchema(Schema):
    class Meta:
        model = Profile
        fields = ["username", "email", "first_name", "last_name"]
