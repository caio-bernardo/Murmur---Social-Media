from datetime import datetime
from typing import Optional
from ninja import FilterSchema, Schema, ModelSchema, Field
from pydantic import field_validator

from posts.models import Post


class PostCreate(Schema):
    content: str = Field(max_length=280)

    @field_validator("content", mode="after")
    @classmethod
    def content_fits(cls, v, values, **kwargs):
        if "content" in values.data:
            content = values.data["content"]
            if len(content) > 280:
                raise ValueError(f"Content doesn't fit. It's size is: {len(content)}")
        return v


class PostPublic(ModelSchema):
    class Meta:
        model = Post
        fields = ["content", "author", "created_at"]

# Only the author can see this info
class PostPrivate(ModelSchema):
    class Meta:
        model = Post
        fields = ["content", "author", "created_at"]

class PostFilter(FilterSchema):
    author: Optional[int] = None
    created_after: Optional[datetime] = Field(None, q='created_at__gte') #type: ignore
