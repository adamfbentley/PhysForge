"""Initial migration for job orchestration service

Revision ID: 001_initial
Revises:
Create Date: 2025-01-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('rq_job_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('results_path', sa.String(), nullable=True),
        sa.Column('logs_path', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('feature_library_path', sa.String(), nullable=True),
        sa.Column('canonical_equation', sa.Text(), nullable=True),
        sa.Column('equation_metrics', sa.JSON(), nullable=True),
        sa.Column('uncertainty_metrics', sa.JSON(), nullable=True),
        sa.Column('sensitivity_analysis_results_path', sa.String(), nullable=True),
        sa.Column('model_ranking_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_owner_id'), 'jobs', ['owner_id'], unique=False)

    # Create job_status_logs table
    op.create_table('job_status_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_status_logs_id'), 'job_status_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('job_status_logs')
    op.drop_table('jobs')