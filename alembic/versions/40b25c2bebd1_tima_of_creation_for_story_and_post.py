"""tima of creation for story and post

Revision ID: 40b25c2bebd1
Revises: 6cfce0f49d4c
Create Date: 2024-06-16 13:34:09.266537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40b25c2bebd1'
down_revision: Union[str, None] = '6cfce0f49d4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('date_of_creation', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_post_date_of_creation'), 'post', ['date_of_creation'], unique=False)
    op.add_column('stories', sa.Column('date_of_creation', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_stories_date_of_creation'), 'stories', ['date_of_creation'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_stories_date_of_creation'), table_name='stories')
    op.drop_column('stories', 'date_of_creation')
    op.drop_index(op.f('ix_post_date_of_creation'), table_name='post')
    op.drop_column('post', 'date_of_creation')
    # ### end Alembic commands ###