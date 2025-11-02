"""add PRPSA assessment model and prpsa_completed field to speech

Revision ID: 67078bd7b589
Revises: fbe75b5e6c6f
Create Date: 2025-11-02 16:05:31.796663

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67078bd7b589'
down_revision = 'fbe75b5e6c6f'
branch_labels = None
depends_on = None


def upgrade():
    # Add prpsa_completed field to speeches table
    with op.batch_alter_table('speeches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prpsa_completed', sa.Boolean(), nullable=False, server_default='false'))

    # Create prpsa_assessments table
    op.create_table('prpsa_assessments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('speech_id', sa.Integer(), nullable=False),
    sa.Column('q1', sa.Integer(), nullable=False),
    sa.Column('q2', sa.Integer(), nullable=False),
    sa.Column('q3', sa.Integer(), nullable=False),
    sa.Column('q4', sa.Integer(), nullable=False),
    sa.Column('q5', sa.Integer(), nullable=False),
    sa.Column('q6', sa.Integer(), nullable=False),
    sa.Column('q7', sa.Integer(), nullable=False),
    sa.Column('q8', sa.Integer(), nullable=False),
    sa.Column('q9', sa.Integer(), nullable=False),
    sa.Column('q10', sa.Integer(), nullable=False),
    sa.Column('q11', sa.Integer(), nullable=False),
    sa.Column('q12', sa.Integer(), nullable=False),
    sa.Column('q13', sa.Integer(), nullable=False),
    sa.Column('q14', sa.Integer(), nullable=False),
    sa.Column('q15', sa.Integer(), nullable=False),
    sa.Column('q16', sa.Integer(), nullable=False),
    sa.Column('q17', sa.Integer(), nullable=False),
    sa.Column('q18', sa.Integer(), nullable=False),
    sa.Column('q19', sa.Integer(), nullable=False),
    sa.Column('q20', sa.Integer(), nullable=False),
    sa.Column('q21', sa.Integer(), nullable=False),
    sa.Column('q22', sa.Integer(), nullable=False),
    sa.Column('q23', sa.Integer(), nullable=False),
    sa.Column('q24', sa.Integer(), nullable=False),
    sa.Column('q25', sa.Integer(), nullable=False),
    sa.Column('q26', sa.Integer(), nullable=False),
    sa.Column('q27', sa.Integer(), nullable=False),
    sa.Column('q28', sa.Integer(), nullable=False),
    sa.Column('q29', sa.Integer(), nullable=False),
    sa.Column('q30', sa.Integer(), nullable=False),
    sa.Column('q31', sa.Integer(), nullable=False),
    sa.Column('q32', sa.Integer(), nullable=False),
    sa.Column('q33', sa.Integer(), nullable=False),
    sa.Column('q34', sa.Integer(), nullable=False),
    sa.Column('total_score', sa.Integer(), nullable=False),
    sa.Column('anxiety_level', sa.String(length=20), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['speech_id'], ['speeches.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('speech_id')
    )
    
    # Create indexes
    with op.batch_alter_table('prpsa_assessments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_prpsa_assessments_speech_id'), ['speech_id'], unique=False)


def downgrade():
    # Drop prpsa_assessments table
    with op.batch_alter_table('prpsa_assessments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_prpsa_assessments_speech_id'))
    
    op.drop_table('prpsa_assessments')
    
    # Remove prpsa_completed field from speeches table
    with op.batch_alter_table('speeches', schema=None) as batch_op:
        batch_op.drop_column('prpsa_completed')
