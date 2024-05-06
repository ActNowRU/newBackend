""" 

Revision ID: d1ab44c23d9d
Revises: 00643a48d27b
Create Date: 2024-04-12 11:20:44.762125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1ab44c23d9d'
down_revision: Union[str, None] = '00643a48d27b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_likes_active', table_name='likes')
    op.drop_column('likes', 'active')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('likes', sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.create_index('ix_likes_active', 'likes', ['active'], unique=False)
    # ### end Alembic commands ###
