from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from Models.post import Post
from Models.post_likes import PostLike
from Schemas.post import PostBase
from Services.database.post import create_post, get_post_by_id, change_post
from Services.database.redis import verify_token_in_redis
from Services.database.story import get_all_post_story
from Services.database.user import get_user
from database_initializer import get_db
from Models.user import User


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# не работает
@router.post("/create", response_model=PostBase)
def create_post_endpoint(post: PostBase,
                         token: str = Depends(oauth2_scheme),
                         db: Session = Depends(get_db)):
    if verify_token_in_redis(token):
        return create_post(session=db, post=post, token=token)
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/get/{post_id}", response_model=PostBase)
def get_post(post_id: int, db: Session = Depends(get_db)):
    try:
        post = get_post_by_id(db, post_id=post_id)
        return post
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Пост не найден")


@router.get("/get_all", response_model=List[PostBase])
def get_all_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()


@router.delete("/delete/{post_id}")
def delete_post(post_id: int,
                db: Session = Depends(get_db),
                token: str = Depends(oauth2_scheme)):
    if verify_token_in_redis(token):
        post = get_post_by_id(db, post_id=post_id)
        user = User.get_current_user_by_token(token)
        user_id = user['id']
        if post.owner_id != user_id:
            raise HTTPException(status_code=403, detail="У вас нет прав на удаление этого поста")
        if post is None:
            raise HTTPException(status_code=404, detail="Пост не найден")
        stroys = get_all_post_story(db, post_id=post_id)
        for story in stroys:
            db.delete(story)
        db.delete(post)
        db.commit()
        return {"message": "Пост  и истории к нему успешно удалены "}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.patch("/update/{post_id}")
def update_post(post_id: int,
                postscheme: PostBase,
                db: Session = Depends(get_db),
                token: str = Depends(oauth2_scheme)):
    if verify_token_in_redis(token):
        post = get_post_by_id(session=db, post_id=post_id)
        user = User.get_current_user_by_token(token)
        user_id = user["id"]
        if post.owner_id != user_id:
            raise HTTPException(status_code=403, detail="У вас нет прав на изменение этого поста")
        if post is None:
            raise HTTPException(status_code=404, detail="Пост не найден")
        change_post(session=db, post_id=post_id, post=postscheme)
        return {"message": "Пост изменен"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.post("/like_post/{post_id}")
def create_and_delete_like(
        post_id: int,
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
):
    if verify_token_in_redis(token):
        post = db.query(Post).filter(Post.id == post_id).first()
        current_user = User.get_current_user_by_token(token)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post_like = db.query(PostLike).filter(PostLike.owner_id == current_user["id"], PostLike.post_id == post_id).first()
        if post_like:
            db.delete(post_like)
            db.commit()
            return {"message": "Like deleted successfully"}
        elif not post_like:
            new_post_like = PostLike(owner_id= current_user["id"], post_id=post_id)
            db.add(new_post_like)
            db.commit()
            return {"message": "Like added successfully"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/post_likes_count/{post_id}")
def get_likes_count(
        post_id: int,
        db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    likes_count = db.query(PostLike).filter(PostLike.post_id == post_id).count()
    return {"likes_count": likes_count}


@router.get("/post_likes_user/{user_name}")
def get_user_post_likes(username:str,
                        db: Session = Depends(get_db)):
    user = get_user(db, user_name=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    likes = db.query(PostLike).filter(PostLike.owner_id == user.id).all()
    if not user:
        raise HTTPException(status_code=404, detail="Likes not found")
    return {"user_post_likes": likes}

