""" 

Revision ID: 407f2b1fb33c
Revises: a17564b470ad
Create Date: 2024-04-16 18:47:50.252486

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '407f2b1fb33c'
down_revision: Union[str, None] = 'a17564b470ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('subscriber_id', sa.Integer(), nullable=False),
    sa.Column('subscribed_to_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['subscribed_to_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['subscriber_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id', 'subscriber_id', 'subscribed_to_id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    # ### end Alembic commands ###
