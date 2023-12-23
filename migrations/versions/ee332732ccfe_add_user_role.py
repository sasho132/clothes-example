"""add user role

Revision ID: ee332732ccfe
Revises: eec420cbc2b6
Create Date: 2023-12-19 19:33:00.242491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ee332732ccfe'
down_revision: Union[str, None] = 'eec420cbc2b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    user_role = postgresql.ENUM('super_admin', 'admin', 'user', name='user_role')
    user_role.create(op.get_bind())
    op.add_column('users', sa.Column('role', sa.Enum('super_admin', 'admin', 'user', name='user_role'), server_default='user', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'role')
    # ### end Alembic commands ###