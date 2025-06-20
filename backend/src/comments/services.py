from django.shortcuts import aget_object_or_404
from ninja.errors import HttpError
from comments.models import Comment
from posts.models import Post
from comments.schemas import CommentCreate, CommentFilter


class CommentService:
    """Service class for managing comment operations."""

    @staticmethod
    async def create_comment(request, payload: CommentCreate) -> Comment:
        """
        Create a new comment on a post.

        Args:
            request: HTTP request object containing authentication information
            payload: Comment creation data including content and post_id

        Returns:
            The newly created Comment instance

        Raises:
            HttpError: If content is empty or post doesn't exist
        """
        try:
            if not payload.content or payload.content.strip() == "":
                raise HttpError(422, "Content cannot be empty")
            # Optionally enforce a max length, e.g. 280 chars
            if len(payload.content) > 280:
                raise HttpError(422, "Content exceeds 280 characters")
            # Ensure the post exists
            post = await aget_object_or_404(Post.objects, pk=payload.post_id)
            comment = Comment(content=payload.content, post=post, author=request.auth)
            await comment.asave()
            return comment
        except HttpError as e:
            raise e
        except Exception as e:
            raise HttpError(500, f"Failed to create comment: {e}")

    @staticmethod
    async def get_all(request, filters: CommentFilter):
        """
        Get all comments, with optional filtering.

        Args:
            request: HTTP request object
            filters: Filter parameters for comments (post, author, created_after)

        Returns:
            Filtered queryset of Comment objects
        """
        comments = Comment.objects.all()
        return filters.filter(comments)

    @staticmethod
    async def get_one_comment(request, id: int) -> Comment:
        """
        Get a single comment by its ID.

        Args:
            request: HTTP request object
            id: The ID of the comment to retrieve

        Returns:
            The requested Comment instance

        Raises:
            HttpError: If comment doesn't exist or retrieval fails
        """
        try:
            comment = await aget_object_or_404(
                Comment.objects.select_related("author"), pk=id
            )
            return comment
        except HttpError as e:
            raise e
        except Exception:
            raise HttpError(500, "Failed to retrieve the comment")

    @staticmethod
    async def delete_comment(request, id: int) -> None:
        """
        Delete a comment by its ID.

        Args:
            request: HTTP request object containing authentication information
            id: The ID of the comment to delete

        Raises:
            HttpError: If comment doesn't exist, user isn't the author,
                      or deletion fails
        """
        comment = await aget_object_or_404(
            Comment.objects.select_related("author"), pk=id
        )
        if request.auth != comment.author:
            raise HttpError(403, "YOU cannot delete comments from another person")
        await comment.adelete()
