from sqlalchemy.orm import Session
from Models.post import Post
from Schemas.post import PostBase
from Models.user import User
from datetime import datetime


def create_post(session: Session, post: PostBase, token: str):
    curent_user = User.get_current_user_by_token(token)
    owner_id = curent_user['id']
    date_of_creation = datetime.now()
    db_post = Post(**post.dict(), owner_id=owner_id, date_of_creation=date_of_creation)
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post


def get_post_by_id(session: Session, post_id: int):
    return session.query(Post).filter(Post.id == post_id).one()


def get_all_user_posts(session: Session, owner_id: int):
    return session.query(Post).filter(Post.owner_id == owner_id).all()


def change_post(session: Session, post_id: int, post: PostBase):
    db_post = session.query(Post).filter(Post.id == post_id).one()
    for key, value in post.dict().items():
        if key != 'owmer_id':
            setattr(db_post, key, value)
    session.commit()
    session.refresh(db_post)
    return db_post
