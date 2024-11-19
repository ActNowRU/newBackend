from fastapi import APIRouter

from app.routers import user, goal, auth, organization, barcode, search
from app.routers import story

root_router = APIRouter()

root_router.include_router(auth.router, prefix="/auth", tags=["Authorization"])
root_router.include_router(user.router, prefix="/user", tags=["User profiles"])
root_router.include_router(
    organization.router, prefix="/organization", tags=["Organizations"]
)
root_router.include_router(
    goal.router, prefix="/goals", tags=["Organization proposals"]
)
root_router.include_router(story.router, prefix="/stories", tags=["User reviews"])
root_router.include_router(search.router, prefix="/search", tags=["Search"])
root_router.include_router(
    barcode.router, prefix="/barcode", tags=["Barcode generator"]
)
