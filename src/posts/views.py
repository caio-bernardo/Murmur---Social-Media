from ninja import Query, Router
from ninja.pagination import paginate
from app.security import AsyncTokenBasedAuth
from posts.schemas import PostCreate, PostFilter, PostPrivate, PostPublic
from posts.services import PostService

# Create your views here.

router = Router()

@router.post("/", auth=AsyncTokenBasedAuth(), response={201: PostPrivate})
async def create_post(request, payload: PostCreate):
    """
    Create a new post.
    """
    return 201, await PostService.create_post(request, payload)

@router.get("/", response=list[PostPublic])
@paginate
async def get_list_of_posts(request, filters: PostFilter = Query(...)): # type: ignore
    """
    Get a list of posts with optional filtering.
    """
    return await PostService.get_all(request, filters)

@router.get("/{int:id}", auth=AsyncTokenBasedAuth(), response=PostPublic)
async def get_a_single_post(request, id: int):
    """
    Get a single post by its ID.
    """
    return await PostService.get_one_post(request, id)

@router.delete("/{int:id}", auth=AsyncTokenBasedAuth(), response={205: None})
async def delete_post(request, id: int):
    """
    Delete a post by its ID.
    """
    await PostService.delete_post(request, id)
    return 205, None