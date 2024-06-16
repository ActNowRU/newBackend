from sqlalchemy.orm import Session
from Models.story import Story
from Models.user import User
from Schemas.story import StoryCreateSchema, StoryChangeSchema
from datetime import datetime


def create_story(session: Session, story: StoryCreateSchema, token: str):
    current_user = User.get_current_user_by_token(token)
    owner_id = current_user['id']
    date_of_creation = datetime.now()
    db_story = Story(**story.dict(), owner_id=owner_id, date_of_creation=date_of_creation)
    session.add(db_story)
    session.commit()
    session.refresh(db_story)
    return db_story


def get_story_by_id(session: Session, story_id: int):
    return session.query(Story).filter(Story.id == story_id).one()


def get_all_user_stories(session: Session, owner_id: int):
    return session.query(Story).filter(Story.owner_id == owner_id).all()


def get_all_post_story(session: Session, post_id: int):
    return session.query(Story).filter(Story.post_id == post_id).all()


def change_story(session: Session, story_id, story: StoryChangeSchema):
    db_story = session.query(Story).filter(Story.id == story_id).one()
    for key, value in story.dict().items():
        if key not in ['owner_id', 'post_id']:
            setattr(db_story, key, value)
    session.commit()
    session.refresh(db_story)
    return db_story


