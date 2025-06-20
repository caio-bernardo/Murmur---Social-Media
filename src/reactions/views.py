from ninja import Query, Router
from ninja.pagination import paginate
from app.security import AsyncTokenBasedAuth
from reactions.schemas import ReactionCreate, ReactionFilter, ReactionPublic, ReactionCount
from reactions.services import ReactionService

router = Router()

@router.post("/", auth=AsyncTokenBasedAuth(), response={201: ReactionPublic})
async def create_reaction(request, payload: ReactionCreate):
    """
    Create or update a reaction (like/dislike) on a post.
    Requires authentication. Returns the created or updated reaction.
    """
    return 201, await ReactionService.create_reaction(request, payload)

@router.delete("/{int:post_id}", auth=AsyncTokenBasedAuth(), response={204: None})
async def delete_reaction(request, post_id: int):
    """
    Delete a user's reaction to a post.
    Requires authentication. Only the user who created the reaction can delete it.
    """
    await ReactionService.delete_reaction(request, post_id)
    return 204, None

@router.get("/", response=list[ReactionPublic])
@paginate
async def get_list_of_reactions(request, filters: ReactionFilter = Query(...)):  # type: ignore
    """
    Get a paginated list of reactions.
    Can be filtered by post, user, reaction type, and creation date.
    """
    return await ReactionService.get_all(request, filters)

@router.get("/posts/{int:post_id}/count", response=ReactionCount)
async def get_reaction_counts(request, post_id: int):
    """
    Get the count of likes and dislikes for a specific post.
    """
    return await ReactionService.get_reaction_counts(request, post_id)

@router.get("/posts/{int:post_id}/my-reaction", auth=AsyncTokenBasedAuth(), response=ReactionPublic)
async def get_user_reaction(request, post_id: int):
    """
    Get the authenticated user's reaction to a specific post.
    Requires authentication.
    """
    return await ReactionService.get_user_reaction(request, post_id)