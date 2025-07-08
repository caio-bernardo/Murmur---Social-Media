from datetime import datetime
from typing import Optional
from ninja import Field, FilterSchema, ModelSchema, Schema

from comments.models import Comment


class CommentCreate(Schema):
    """
    Schema for creating a new comment.
    Requires the comment content and the ID of the post being commented on.
    """

    content: str
    post_id: int


class CommentPublic(ModelSchema):
    """
    Public schema for comment data.
    Exposes content, author, associated post, and creation timestamp.
    """

    class Meta:
        model = Comment
        fields = ["content", "author", "post", "created_at"]


class CommentFilter(FilterSchema):
    """
    Filter schema for comments.
    Supports filtering by post ID, author ID, and comments created after a specific datetime.
    """

    post: Optional[int] = None
    author: Optional[int] = None
    created_after: Optional[datetime] = Field(None, q="created_at__gte")  # type: ignore
