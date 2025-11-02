"""Add session_number field to sessions table

Revision ID: session_number_add
Revises: 9f38a95fea6c
Create Date: 2025-11-02 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'session_number_add'
down_revision = '9f38a95fea6c'
branch_labels = None
depends_on = None

def upgrade():
    # Add session_number column to sessions table
    with op.batch_alter_table('sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('session_number', sa.Integer(), nullable=False, server_default='1'))
    
    # Remove server default after adding the column
    with op.batch_alter_table('sessions', schema=None) as batch_op:
        batch_op.alter_column('session_number', server_default=None)

def downgrade():
    # Remove session_number column from sessions table
    with op.batch_alter_table('sessions', schema=None) as batch_op:
        batch_op.drop_column('session_number')
