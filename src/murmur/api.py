# from ninja_jwt.routers.blacklist import blacklist_router
from ninja_jwt.routers.obtain import obtain_pair_router  # , sliding_router

# from ninja_jwt.routers.verify import verify_router
from ninja import NinjaAPI

# Import routers
from apps.accounts.apis import router as accounts_router
from apps.posts.apis import router as posts_router
from apps.comments.apis import router as comments_router
from apps.reactions.apis import router as reactions_router

app = NinjaAPI()

app.add_router("/token", tags=["Auth"], router=obtain_pair_router)
app.add_router("/accounts", tags=["Account"], router=accounts_router)
app.add_router("/posts", tags=["Posts"], router=posts_router)
app.add_router("/comments", tags=["Comment"], router=comments_router)
app.add_router("/reactions", tags=["Reaction"], router=reactions_router)


@app.get("/")
async def checkhealth(request):
    return {"detail": "API is on the air"}
