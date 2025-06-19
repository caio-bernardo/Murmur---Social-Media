from ninja import Query, Router
from ninja.pagination import paginate
from app.security import TokenBasedAuth
from reactions.schemas import ReactionCreate, ReactionFilter, ReactionPublic, ReactionCount
from reactions.services import ReactionService

router = Router()

@router.post("/", auth=TokenBasedAuth(), response={201: ReactionPublic})
def create_reaction(request, payload: ReactionCreate):
    """
    Create or update a reaction (like/dislike) on a post.
    Requires authentication. Returns the created or updated reaction.
    """
    return 201, ReactionService.create_reaction(request, payload)

@router.delete("/{int:post_id}", auth=TokenBasedAuth(), response={204: None})
def delete_reaction(request, post_id: int):
    """
    Delete a user's reaction to a post.
    Requires authentication. Only the user who created the reaction can delete it.
    """
    ReactionService.delete_reaction(request, post_id)
    return 204, None

@router.get("/", response=list[ReactionPublic])
@paginate
def get_list_of_reactions(request, filters: ReactionFilter = Query(...)):  # type: ignore
    """
    Get a paginated list of reactions.
    Can be filtered by post, user, reaction type, and creation date.
    """
    return ReactionService.get_all(request, filters)

@router.get("/posts/{int:post_id}/count", response=ReactionCount)
def get_reaction_counts(request, post_id: int):
    """
    Get the count of likes and dislikes for a specific post.
    """
    return ReactionService.get_reaction_counts(request, post_id)

@router.get("/posts/{int:post_id}/my-reaction", auth=TokenBasedAuth(), response=ReactionPublic)
def get_user_reaction(request, post_id: int):
    """
    Get the authenticated user's reaction to a specific post.
    Requires authentication.
    """
    return ReactionService.get_user_reaction(request, post_id)
