from fastapi import APIRouter

from routers import user, goal, story, auth, organization

root_router = APIRouter()

root_router.include_router(auth.router, prefix="/auth", tags=["Authorization"])
root_router.include_router(user.router, prefix="/user", tags=["User profiles"])
root_router.include_router(
    organization.router, prefix="/organization", tags=["Organizations"]
)
root_router.include_router(
    goal.router, prefix="/goals", tags=["Organization proposals"]
)
root_router.include_router(story.router, prefix="/story", tags=["User reviews"])
