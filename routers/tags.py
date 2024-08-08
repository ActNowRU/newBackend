from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.database.methods import tags
from services.database.models.post import Post
from services.database.models.story import Story
from services.database.models.tags import Tags
from services.database.models.user import User
from services.database.redis import check_token_status
from services.database.schemas.tags import Tag, TagBase

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/tags", response_model=Tag)
async def create_tag(
        tag: TagBase,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    try:
        await tags.create_tag(tag=tag, session=db)
        return {"Tag created"}
    except:
        HTTPException(status_code=404, detail="Ошибка при создании тэга")


@router.get("/all_tags")
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Tags))
        return result.scalars().all()
    except:
        HTTPException(status_code=404, detail="ошибка при поиске тэгов")


@router.post("/user_tag")
async def user_tag(
        tag_id: int, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    if await check_token_status(token):
        user = User.get_current_user_by_token(token)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user["id"]
        tag_result = await db.execute(select(Tags).filter(Tags.id == tag_id))
        tag = tag_result.scalars().one()
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        try:
            user_result = await db.execute(select(User).filter(User.id == user_id))
            user = user_result.scalars().one()
            user.tags.append(tag)

            await db.commit()
            return {"message": f"Tag {tag.name} assigned to user {user_id}"}
        except:
            HTTPException(status_code=404, detail="Ошибка добавления тэга")
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.post("/post_tag")
async def post_tag(
        tag_id: int,
        post_id: int,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    tag_result = await db.execute(select(Tags).filter(Tags.id == tag_id))
    tag = tag_result.scalars().one()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    post_result = await db.execute(select(Post).filter(Post.id == post_id))
    post = post_result.scalars().one()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        post.tags.append(tag)
        await db.commit()
        return {"message": f"Tag {tag.name} assigned to post {post_id}"}
    except:
        HTTPException(status_code=404, detail="Ошибка добавления тэга")


@router.post("/story_tag")
async def story_tag(
        tag_id: int,
        story_id: int,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    tag_result = await db.execute(select(Tags).filter(Tags.id == tag_id))
    tag = tag_result.scalars().one()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    story = story_result.scalars().one()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    try:
        story.tags.append(tag)
        await db.commit()
        return {"message": f"Tag {tag.name} assigned to story {story_id}"}
    except:
        HTTPException(status_code=404, detail="Ошибка добавления тэга")
