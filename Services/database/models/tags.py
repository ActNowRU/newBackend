from sqlalchemy import Table, Column, Integer, ForeignKey, String, UniqueConstraint

from database_initializer import Base


class Tags(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(255), nullable=False, index=True)
    name = Column(String, unique=True)


user_tags = Table(
    "user_tags",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
    UniqueConstraint("user_id", "tag_id"),
)

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
    UniqueConstraint("post_id", "tag_id"),
)

story_tags = Table(
    "story_tags",
    Base.metadata,
    Column("story_id", Integer, ForeignKey("stories.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
    UniqueConstraint("story_id", "tag_id"),
)
