from ninja.router import Router
from accounts.schemas import UserProfilePublicSchema, UserRegisterInSchema,  UserRegisterOutSchema
from app.security import TokenBasedAuth
# Create your views here.

router = Router()

@router.get("/me", auth=TokenBasedAuth, response=UserProfilePublicSchema)
def get_user_profile(request):
    """
    Get private version of a user's profile
    """
    pass

@router.get("/{username}")
def get_public_user(request, username: str):
    """
    See public version of a user's profile
    """
    pass

@router.post("/register", response= UserRegisterOutSchema)
def create_user(request, payload: UserRegisterInSchema):
    """
    Register a new user
    """
    pass
