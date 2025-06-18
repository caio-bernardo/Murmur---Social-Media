from ninja import Field
from ninja.schema import Schema
from ninja_jwt.schema import TokenRefreshOutputSchema
from pydantic import EmailStr, validator
from pydantic.types import SecretStr

from accounts.models import UserProfile

class UserProfilePublicSchema(Schema):
    pass

class UserProfilePrivateSchema(Schema):
    pass

class UserRegisterInSchema(Schema):
    username: str = Field(..., description="Name of the user")
    email: EmailStr = Field(..., description="User's email address")
    password: SecretStr = Field(..., min_length=8, max_length=24, description="User's password. Must be at least 8 characters long.")
    password_confirm: SecretStr

    @validator("password_confirm")
    def password_match(cls, v, values, **kwargs):
        if 'password' in values and v != values["password"]:
            raise ValueError("Passwords don't match.")
        return v

class  UserRegisterOutSchema(Schema):
    pass
