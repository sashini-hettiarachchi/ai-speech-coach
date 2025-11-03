"""add_cascade_delete_constraints

Revision ID: e790fd466542
Revises: session_number_add
Create Date: 2025-11-03 22:11:23.459823

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e790fd466542'
down_revision = 'session_number_add'
branch_labels = None
depends_on = None


def upgrade():
    # Update sessions table foreign key constraint
    op.drop_constraint('sessions_speech_id_fkey', 'sessions', type_='foreignkey')
    op.create_foreign_key(
        'sessions_speech_id_fkey', 
        'sessions', 
        'speeches', 
        ['speech_id'], 
        ['id'], 
        ondelete='CASCADE'
    )
    
    # Update prpsa_assessments table foreign key constraint
    op.drop_constraint('prpsa_assessments_speech_id_fkey', 'prpsa_assessments', type_='foreignkey')
    op.create_foreign_key(
        'prpsa_assessments_speech_id_fkey', 
        'prpsa_assessments', 
        'speeches', 
        ['speech_id'], 
        ['id'], 
        ondelete='CASCADE'
    )


def downgrade():
    # Revert sessions table foreign key constraint
    op.drop_constraint('sessions_speech_id_fkey', 'sessions', type_='foreignkey')
    op.create_foreign_key(
        'sessions_speech_id_fkey', 
        'sessions', 
        'speeches', 
        ['speech_id'], 
        ['id']
    )
    
    # Revert prpsa_assessments table foreign key constraint
    op.drop_constraint('prpsa_assessments_speech_id_fkey', 'prpsa_assessments', type_='foreignkey')
    op.create_foreign_key(
        'prpsa_assessments_speech_id_fkey', 
        'prpsa_assessments', 
        'speeches', 
        ['speech_id'], 
        ['id']
    )
