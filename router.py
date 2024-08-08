from fastapi import APIRouter

from routers import user, post, stories, auth, complaints, tags

root_router = APIRouter()

root_router.include_router(user.router, prefix="/user", tags=["user"])
root_router.include_router(post.router, prefix="/post", tags=["post"])
root_router.include_router(stories.router, prefix="/stories", tags=["stories"])
root_router.include_router(auth.router, prefix="/auth", tags=["auth"])
root_router.include_router(complaints.router, prefix="/complaint", tags=["complaints"])
root_router.include_router(tags.router, prefix="/tag", tags=["tags"])
