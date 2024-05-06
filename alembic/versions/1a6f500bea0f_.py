""" 

Revision ID: 1a6f500bea0f
Revises: 17a8a6a3c4ee
Create Date: 2024-04-15 12:31:42.740347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a6f500bea0f'
down_revision: Union[str, None] = '17a8a6a3c4ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('content', sa.ARRAY(sa.String()), nullable=True))
    op.drop_index('ix_post_typing.List', table_name='post')
    op.create_index(op.f('ix_post_content'), 'post', ['content'], unique=False)
    op.drop_column('post', 'typing.List')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('typing.List', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_post_content'), table_name='post')
    op.create_index('ix_post_typing.List', 'post', ['typing.List'], unique=False)
    op.drop_column('post', 'content')
    # ### end Alembic commands ###
