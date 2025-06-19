# Create your views here.
from ninja import Query, Router
from ninja.pagination import paginate
from app.security import TokenBasedAuth
from comments.schemas import CommentCreate, CommentFilter, CommentPublic
from comments.services import CommentService

router = Router()

@router.post("/", auth=TokenBasedAuth(), response={201: CommentPublic})
def create_comment(request, payload: CommentCreate):
    """
    Create a new comment on a post.
    Requires authentication. Returns the newly created comment.
    """
    return 201, CommentService.create_comment(request, payload)

@router.get("/", response=list[CommentPublic])
@paginate
def get_list_of_comments(request, filters: CommentFilter = Query(...)):  # type: ignore
    """
    Get a paginated list of comments.
    Can be filtered by post, author, and creation date.
    """
    return CommentService.get_all(request, filters)

@router.get("/{int:id}", response=CommentPublic)
def get_a_single_comment(request, id: int):
    """
    Get a single comment by its ID.
    Returns 404 if the comment doesn't exist.
    """
    return CommentService.get_one_comment(request, id)

@router.delete("/{int:id}", auth=TokenBasedAuth(), response={205: None})
def delete_comment(request, id: int):
    """
    Delete a comment by its ID.
    Requires authentication. Only the author of the comment can delete it.
    Returns 403 if the authenticated user isn't the author.
    """
    CommentService.delete_comment(request, id)
