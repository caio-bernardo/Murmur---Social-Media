# Create your views here.
from ninja import Query, Router
from ninja.pagination import paginate
from app.security import AsyncTokenBasedAuth
from comments.schemas import CommentCreate, CommentFilter, CommentPublic
from comments.services import CommentService

router = Router()

@router.post("/", auth=AsyncTokenBasedAuth(), response={201: CommentPublic})
async def create_comment(request, payload: CommentCreate):
    """
    Create a new comment on a post.
    Requires authentication. Returns the newly created comment.
    """
    return 201, await CommentService.create_comment(request, payload)

@router.get("/", response=list[CommentPublic])
@paginate
async def get_list_of_comments(request, filters: CommentFilter = Query(...)):  # type: ignore
    """
    Get a paginated list of comments.
    Can be filtered by post, author, and creation date.
    """
    return await CommentService.get_all(request, filters)

@router.get("/{int:id}", response=CommentPublic)
async def get_a_single_comment(request, id: int):
    """
    Get a single comment by its ID.
    Returns 404 if the comment doesn't exist.
    """
    return await CommentService.get_one_comment(request, id)

@router.delete("/{int:id}", auth=AsyncTokenBasedAuth(), response={205: None})
async def delete_comment(request, id: int):
    """
    Delete a comment by its ID.
    Requires authentication. Only the author of the comment can delete it.
    Returns 403 if the authenticated user isn't the author.
    """
    await CommentService.delete_comment(request, id)
    return 205, None