from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from Models.story import Story
from Models.story_likes import Like
from Models.user import User
from Schemas.story import StoryCreateSchema, StoryChangeSchema
from Services.database.story import get_story_by_id, create_story, get_all_user_stories, change_story
from Services.database.user import get_user
from database_initializer import get_db
from typing import List
from Services.database.redis import verify_token_in_redis
from sqlalchemy.orm.exc import NoResultFound

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/stories", response_model=StoryCreateSchema)
def create_story_endpoint(story: StoryCreateSchema,
                          token: str = Depends(oauth2_scheme),
                          db: Session = Depends(get_db)):
    if verify_token_in_redis(token):
        try:
            create_story(session=db, story=story, token=token)
            return {"История создана"}
        except:
            HTTPException(status_code=403, detail="Данные ведены не верно")
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/get_stories", response_model=List[StoryCreateSchema])
def get_all_stories(db: Session = Depends(get_db)):
    try:
        return db.query(Story).all()
    except: HTTPException(status_code=404, detail="Историй нет")


@router.get("/stories/{story_id}", response_model=StoryCreateSchema)
def read_story(story_id: int, db: Session = Depends(get_db)):
    try:
        story = get_story_by_id(db, story_id=story_id)
        if story is None:
            raise HTTPException(status_code=404, detail="История не найдена")
        return story
    except NoResultFound:
        raise HTTPException(status_code=404, detail="История не найдена")


@router.get("/stories_by_username/{username}", response_model=List[StoryCreateSchema])
def read_user_stories(username: str, db: Session = Depends(get_db)):
    user = get_user(db, user_name=username)

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    try:
        stories = get_all_user_stories(db, owner_id=user.id)
        return stories
    except NoResultFound:
        raise HTTPException(status_code=404, detail="История не найдена")


@router.delete("/delete/{story_id}")
def delete_story(story_id: int,
                 db: Session = Depends(get_db),
                 token: str = Depends(oauth2_scheme)):
    if verify_token_in_redis(token):
        story = get_story_by_id(db, story_id=story_id)
        user = User.get_current_user_by_token(token)
        user_id = user['id']

        if story.owner_id != user_id:
            raise HTTPException(status_code=403, detail="У вас нет прав на удаление этого поста")

        if story is None:
            raise HTTPException(status_code=404, detail="История не найдена")

        db.delete(story)
        db.commit()
        return {"message": "История успешно удалена"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.patch("/stories_change/{story_id}")
def update_story(
        story_id: int,
        storyscheme: StoryChangeSchema,
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)):
    if verify_token_in_redis(token):
        story = get_story_by_id(db, story_id=story_id)
        user = User.get_current_user_by_token(token)
        user_id = user["id"]
        if story.owner_id != user_id:
            raise HTTPException(status_code=403, detail="У вас нет прав на изменение этой истории")
        if story is None:
            raise HTTPException(status_code=404, detail="История не найдена")
        change_story(story_id=story_id, session=db, story=storyscheme)
        return {"message": "История изменена"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.post('/like_story/{story_id}')
def create_and_delete_like(story_id: int,
                           db: Session = Depends(get_db),
                           token: str = Depends(oauth2_scheme),
                           ):
    if verify_token_in_redis(token):
        story = db.query(Story).filter(Story.id == story_id).first()
        current_user = User.get_current_user_by_token(token)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        like = db.query(Like).filter(Like.owner_id == current_user["id"], Like.story_id == story_id).first()
        if like:
            db.delete(like)
            db.commit()
            return {"message": "Like deleted successfully"}
        elif not like:
            new_like = Like(owner_id=current_user["id"], story_id=story_id)
            db.add(new_like)
            db.commit()
            return {"message": "Like added successfully"}
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.get("/likes_count/{story_id}")
def get_likes_count(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    likes_count = db.query(Like).filter(Like.story_id == story_id).count()
    return {"likes_count": likes_count}


@router.get("/story_likes_user/{user_name}")
def get_user_story_likes(username: str,
                         db: Session = Depends(get_db)):
    user = get_user(db, user_name=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    likes = db.query(Like).filter(Like.owner_id == user.id).all()
    if not user:
        raise HTTPException(status_code=404, detail="Likes not found")
    return {"user_story_likes": likes}
