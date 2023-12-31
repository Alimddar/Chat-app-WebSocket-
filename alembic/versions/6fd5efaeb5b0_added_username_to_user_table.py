"""Added username to User table

Revision ID: 6fd5efaeb5b0
Revises: 
Create Date: 2023-10-30 22:37:31.208764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fd5efaeb5b0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.add_column('user', sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.add_column('user', sa.Column('password', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.add_column('user', sa.Column('is_admin', sa.Boolean(), nullable=False))
    op.create_unique_constraint(None, 'user', ['email'])
    op.create_unique_constraint(None, 'user', ['username'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_column('user', 'is_admin')
    op.drop_column('user', 'password')
    op.drop_column('user', 'email')
    op.drop_column('user', 'username')
    # ### end Alembic commands ###
