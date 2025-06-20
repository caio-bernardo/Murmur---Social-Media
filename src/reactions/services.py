from django.shortcuts import aget_object_or_404
from ninja.errors import HttpError
from posts.models import Post
from reactions.models import Reaction, ReactionType
from reactions.schemas import ReactionCreate, ReactionFilter, ReactionCount

class ReactionService:
    """Service class for managing reaction operations."""

    @staticmethod
    async def create_reaction(request, payload: ReactionCreate) -> Reaction:
        """
        Create or update a reaction for a post.
        If the user has already reacted to the post, the reaction is updated.

        Args:
            request: HTTP request object containing authentication information
            payload: Reaction creation data including post_id and reaction_type

        Returns:
            The newly created or updated Reaction instance

        Raises:
            HttpError: If post doesn't exist or reaction_type is invalid
        """
        try:
            if payload.reaction_type not in [ReactionType.LIKE, ReactionType.DISLIKE]:
                raise HttpError(422, f"Invalid reaction type: {payload.reaction_type}")

            # Check if post exists
            post = await aget_object_or_404(Post.objects, pk=payload.post_id)

            # Try to get existing reaction
            reaction = await Reaction.objects.filter(user=request.auth, post=post).afirst()
            if reaction:
                # Update existing reaction
                reaction.reaction_type = payload.reaction_type
                await reaction.asave()
            else:
                # Create new reaction
                reaction = Reaction(
                    user=request.auth,
                    post=post,
                    reaction_type=payload.reaction_type
                )
                await reaction.asave()

            return reaction
        except HttpError as e:
            raise e
        except Exception as e:
            raise HttpError(500, f"Failed to create reaction: {e}")

    @staticmethod
    async def delete_reaction(request, post_id: int) -> None:
        """
        Delete a user's reaction to a post.

        Args:
            request: HTTP request object containing authentication information
            post_id: The ID of the post to delete the reaction from

        Raises:
            HttpError: If the reaction doesn't exist or deletion fails
        """
        # Check if post exists
        post = await aget_object_or_404(Post.objects, pk=post_id)

        # Try to get and delete existing reaction
        reaction = await aget_object_or_404(Reaction.objects.select_related("post"), user=request.auth, post=post)
        await reaction.adelete()

    @staticmethod
    async def get_all(request, filters: ReactionFilter):
        """
        Get all reactions, with optional filtering.

        Args:
            request: HTTP request object
            filters: Filter parameters for reactions

        Returns:
            Filtered queryset of Reaction objects
        """
        reactions = Reaction.objects.all()
        return filters.filter(reactions)

    @staticmethod
    async def get_reaction_counts(request, post_id: int) -> ReactionCount:
        """
        Get the count of likes and dislikes for a post.

        Args:
            request: HTTP request object
            post_id: The ID of the post to get counts for

        Returns:
            ReactionCount object with counts for likes and dislikes

        Raises:
            HttpError: If the post doesn't exist
        """
        try:
            # Check if post exists
            post = await aget_object_or_404(Post.objects, pk=post_id)

            likes = await Reaction.objects.filter(post=post, reaction_type=ReactionType.LIKE).acount()
            dislikes = await Reaction.objects.filter(post=post, reaction_type=ReactionType.DISLIKE).acount()

            return ReactionCount(
                post_id=post.pk,
                likes=likes,
                dislikes=dislikes
            )
        except Exception as e:
            raise HttpError(500, f"Failed to get reaction counts: {e}")

    @staticmethod
    async def get_user_reaction(request, post_id: int) -> Reaction:
        """
        Get a user's reaction to a specific post.

        Args:
            request: HTTP request object containing authentication information
            post_id: The ID of the post to get the reaction for

        Returns:
            The Reaction instance

        Raises:
            HttpError: If the post or reaction doesn't exist
        """
        try:
            # Check if post exists
            post = await aget_object_or_404(Post.objects, pk=post_id)

            # Try to get the reaction
            reaction = await aget_object_or_404(Reaction.objects, user=request.auth, post=post)
            return reaction
        except Exception:
            raise HttpError(404, "Reaction not found")
