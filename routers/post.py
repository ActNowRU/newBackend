from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from database_initializer import get_db
from services.database.methods.post import create_post, get_post_by_id, change_post
from services.database.methods.story import get_all_post_story
from services.database.methods.user import get_user
from services.database.models.post import Post
from services.database.models.post_likes import PostLike
from services.database.models.user import User
from services.database.redis import check_token_status
from services.database.schemas.post import PostBase

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# не работает
@router.post("/create", response_model=PostBase)
async def create_post_endpoint(
        post: PostBase,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
):
    if await check_token_status(token):
        try:
            await create_post(session=db, post=post, token=token)
            return {"post created"}
        except:
            raise HTTPException(status_code=403, detail="Данные введены не верно")
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/get/{post_id}", response_model=PostBase)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    try:
        post = await get_post_by_id(db, post_id=post_id)
        return post
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Пост не найден")


@router.get("/get_all", response_model=List[PostBase])
async def get_all_posts(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Post))
        return result.scalars().all()
    except:
        HTTPException(status_code=404, detail="Голсы не найдены")


@router.delete("/delete/{post_id}")
async def delete_post(
        post_id: int,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        post = await get_post_by_id(db, post_id=post_id)
        user = User.get_current_user_by_token(token)
        user_id = user["id"]
        if post.owner_id != user_id:
            raise HTTPException(
                status_code=403, detail="У вас нет прав на удаление этого поста"
            )
        if post is None:
            raise HTTPException(status_code=404, detail="Пост не найден")
        stroys = await get_all_post_story(db, post_id=post_id)
        for story in stroys:
            await db.delete(story)
        await db.delete(post)
        await db.commit()
        return {"message": "Пост  и истории к нему успешно удалены "}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.patch("/update/{post_id}")
async def update_post(
        post_id: int,
        postscheme: PostBase,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        post = await get_post_by_id(session=db, post_id=post_id)
        user = User.get_current_user_by_token(token)
        user_id = user["id"]
        if post.owner_id != user_id:
            raise HTTPException(
                status_code=403, detail="У вас нет прав на изменение этого поста"
            )
        if post is None:
            raise HTTPException(status_code=404, detail="Пост не найден")
        await change_post(session=db, post_id=post_id, post=postscheme)
        return {"message": "Пост изменен"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.post("/like_post/{post_id}")
async def create_and_delete_like(
        post_id: int,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme),
):
    if await check_token_status(token):
        post_result = await db.execute(select(Post).filter(Post.id == post_id))
        post = post_result.scalars().first()

        current_user = User.get_current_user_by_token(token)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post_like_result = await db.execute(
            select(PostLike).filter(
                PostLike.owner_id == current_user["id"], PostLike.post_id == post_id
            )
        )
        post_like = post_like_result.scalars().first()
        if post_like:
            await db.delete(post_like)
            await db.commit()
            return {"message": "Like deleted successfully"}
        elif not post_like:
            new_post_like = PostLike(owner_id=current_user["id"], post_id=post_id)
            db.add(new_post_like)
            await db.commit()
            return {"message": "Like added successfully"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/post_likes_count/{post_id}")
async def get_likes_count(post_id: int, db: AsyncSession = Depends(get_db)):
    post_result = await db.execute(select(Post).filter(Post.id == post_id))
    post = post_result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    likes_count_result = await db.execute(
        select(PostLike).filter(PostLike.post_id == post_id)
    )
    likes_count = likes_count_result.scalars().all().count()
    return {"likes_count": likes_count}


@router.get("/post_likes_user/{user_name}")
async def get_user_post_likes(username: str, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_name=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    likes_result = await db.execute(
        select(PostLike).filter(PostLike.owner_id == user.id)
    )
    likes = likes_result.scalars().all()
    if not user:
        raise HTTPException(status_code=404, detail="Likes not found")
    return {"user_post_likes": likes}
