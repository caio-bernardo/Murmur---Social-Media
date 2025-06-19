from typing import Union
from ninja import Router
from app.security import TokenBasedAuth
from posts.schemas import PostCreate, PostPrivate, PostPublic
from posts.services import PostService

# Create your views here.

router = Router()

@router.post("/", auth=TokenBasedAuth(), response={201: PostPrivate})
def create_post(request, payload: PostCreate):
    return 201, PostService.create_post(request, payload)

@router.get("/", response=list[PostPublic])
def get_list_of_posts(request): # need query and pagination
    pass

@router.get("/{int:id}", auth=TokenBasedAuth(), response=Union[PostPublic,PostPrivate])
def get_a_single_post(request, id: int):
    return PostService.get_one_post(request, id)

@router.delete("/{int:id}", auth=TokenBasedAuth(), response={205: None})
def delete_post(request, id: int):
    PostService.delete_post(request, id)
