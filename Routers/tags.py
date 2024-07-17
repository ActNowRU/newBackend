from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from Services.database.redis import verify_token_in_redis
from database_initializer import get_db
from Models.tags import Tags
from Schemas.tags import Tag, TagBase
from Services.database import tags
from Models.user import User
from Models.post import Post
from Models.story import Story
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post('/tags', response_model=Tag)
def create_tag(tag: TagBase, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        tags.create_tag(tag=tag, session=db)
        return {"Tag created"}
    except:
        HTTPException(status_code=404, detail="Ошибка при создании тэга")


@router.get('/all_tags')
def get_all_tags(db: Session = Depends(get_db)):
    try:
        return db.query(Tags).all()
    except:
        HTTPException(status_code=404, detail="ошибка при поиске тэгов")



@router.post("/user_tag")
def user_tag(tag_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    if verify_token_in_redis(token):
        user = User.get_current_user_by_token(token)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user["id"]
        tag = db.query(Tags).get(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        try:
            user = db.query(User).get(user_id)
            user.tags.append(tag)
            db.commit()
            return{"message": f"Tag {tag.name} assigned to user {user_id}"}
        except:
            HTTPException(status_code=404, detail="Ошибка добавления тэга")
    else:
        raise HTTPException(status_code=401, detail="Токен устарел")


@router.post("/post_tag")
def post_tag(tag_id: int, post_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    tag = db.query(Tags).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        post.tags.append(tag)
        db.commit()
        return{"message": f"Tag {tag.name} assigned to post {post_id}"}
    except:
        HTTPException(status_code=404, detail="Ошибка добавления тэга")


@router.post("/story_tag")
def story_tag(tag_id: int, story_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    tag = db.query(Tags).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    story = db.query(Story).get(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    try:
        story.tags.append(tag)
        db.commit()
        return{"message": f"Tag {tag.name} assigned to story {story_id}"}
    except:
        HTTPException(status_code=404, detail="Ошибка добавления тэга")

