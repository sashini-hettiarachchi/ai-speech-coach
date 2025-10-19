"""Remove user profile fields

Revision ID: 9b2148c1bd6e
Revises: 8a1047b0ac5d
Create Date: 2025-10-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b2148c1bd6e'
down_revision = '8a1047b0ac5d'
branch_labels = None
depends_on = None


def upgrade():
    # Remove user profile columns
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('family_name')
        batch_op.drop_column('given_name')
        batch_op.drop_column('nickname')
        batch_op.drop_column('picture')
        batch_op.drop_column('name')
        batch_op.drop_column('email')


def downgrade():
    # Add back user profile columns
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('picture', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('nickname', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('given_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('family_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
