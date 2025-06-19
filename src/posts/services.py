from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from posts.models import Post
from posts.schemas import PostCreate, PostPrivate, PostPublic


class PostService: # Should I can Postal service? :D

    @staticmethod
    def create_post(request, payload: PostCreate) -> Post:
        try:
            if payload.content == "":
                raise HttpError(422, "Content cannot be empty")
            return Post.objects.create(content=payload.content, author=request.auth)
        except HttpError as e:
            raise e
        except Exception as e:
            raise HttpError(500, f"Failed to create post: {e}")

    @staticmethod
    def get_one_post(request, id: int) -> PostPublic | PostPrivate:
        try:
            post = get_object_or_404(Post.objects, pk=id)
            if request.auth == post.author:
                return PostPrivate.model_validate(post)
            return PostPublic.model_validate(post)
        except HttpError as e:
                raise e
        except Exception as e:
            raise HttpError(500, "Failed to retrieve the post")


    @staticmethod
    def delete_post(request, id: int) -> None:
        try:
            post = get_object_or_404(Post.objects, pk=id)
            if request.auth != post.author:
                raise HttpError(403, "YOU cannot delete posts from another person")
            post.delete()
        except HttpError as e:
            raise e
        except Exception as e:
            raise HttpError(500, "Failed to delete post")
