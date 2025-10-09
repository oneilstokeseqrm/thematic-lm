"""Initial schema: Analysis and AnalysisCheckpoint tables

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', name='analysisstatus'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('estimated_cost_usd', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('actual_cost_usd', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyses_account_id'), 'analyses', ['account_id'], unique=False)
    op.create_index(op.f('ix_analyses_tenant_id'), 'analyses', ['tenant_id'], unique=False)
    op.create_index('ix_analyses_idempotency', 'analyses', ['account_id', 'idempotency_key'], unique=True)

    # Create analysis_checkpoints table
    op.create_table(
        'analysis_checkpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.String(length=100), nullable=False),
        sa.Column('state_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_checkpoints_analysis_id'), 'analysis_checkpoints', ['analysis_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_analysis_checkpoints_analysis_id'), table_name='analysis_checkpoints')
    op.drop_table('analysis_checkpoints')
    op.drop_index('ix_analyses_idempotency', table_name='analyses')
    op.drop_index(op.f('ix_analyses_tenant_id'), table_name='analyses')
    op.drop_index(op.f('ix_analyses_account_id'), table_name='analyses')
    op.drop_table('analyses')
    op.execute('DROP TYPE analysisstatus')
