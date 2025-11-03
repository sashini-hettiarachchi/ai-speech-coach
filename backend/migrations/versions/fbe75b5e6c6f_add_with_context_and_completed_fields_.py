"""add with_context and completed fields to speech model

Revision ID: fbe75b5e6c6f
Revises: c1d2e3f4g5h6
Create Date: 2025-11-02 15:38:01.441238

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbe75b5e6c6f'
down_revision = 'c1d2e3f4g5h6'
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to speeches table
    with op.batch_alter_table('speeches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('with_context', sa.Boolean(), nullable=False, server_default='true'))
        batch_op.add_column(sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    # Remove the added columns
    with op.batch_alter_table('speeches', schema=None) as batch_op:
        batch_op.drop_column('completed')
        batch_op.drop_column('with_context')
