from typing import Optional
from datetime import datetime
from ninja import Field, FilterSchema, ModelSchema, Schema
from reactions.models import Reaction, ReactionType

class ReactionCreate(Schema):
    """
    Schema for creating a new reaction.
    Requires the post ID and the reaction type (like/dislike).
    """
    post_id: int
    reaction_type: str = ReactionType.LIKE

class ReactionPublic(ModelSchema):
    """
    Public schema for reaction data.
    Exposes user, post, reaction type, and timestamps.
    """
    class Meta:
        model = Reaction
        fields = ['id', 'user', 'post', 'reaction_type', 'created_at', 'updated_at']

class ReactionFilter(FilterSchema):
    """
    Filter schema for reactions.
    Supports filtering by post ID, user ID, reaction type, and creation date.
    """
    post: Optional[int] = None
    user: Optional[int] = None
    reaction_type: Optional[str] = None
    created_after: Optional[datetime] = Field(None, q="created_at__gte")  # type: ignore


class ReactionCount(Schema):
    """
    Schema for counting reactions by type.
    Used for returning like/dislike counts for a post.
    """
    post_id: int
    likes: int
    dislikes: int
