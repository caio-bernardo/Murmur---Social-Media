from django.shortcuts import aget_object_or_404
from ninja.errors import HttpError
from posts.models import Post
from posts.schemas import PostCreate, PostFilter


class PostService:

    @staticmethod
    async def create_post(request, payload: PostCreate) -> Post:
        try:
            if payload.content == "":
                raise HttpError(422, "Content cannot be empty")
            post = Post(content=payload.content, author=request.auth)
            await post.asave()
            return post
        except HttpError as e:
            raise e
        except Exception as e:
            raise HttpError(500, f"Failed to create post: {e}")

    @staticmethod
    async def get_all(request, filters: PostFilter):
        posts = Post.objects.all()
        return filters.filter(posts)

    @staticmethod
    async def get_one_post(request, id: int) -> Post:
        try:
            post = await aget_object_or_404(Post.objects, pk=id)
            return post
        except HttpError as e:
            raise e
        except Exception:
            raise HttpError(500, "Failed to retrieve the post")


    @staticmethod
    async def delete_post(request, id: int) -> None:
        post = await aget_object_or_404(Post.objects.select_related("author"), pk=id)
        if request.auth != post.author:
            raise HttpError(403, "YOU cannot delete posts from another person")
        await post.adelete()
