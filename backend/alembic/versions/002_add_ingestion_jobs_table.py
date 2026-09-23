"""Add ingestion_jobs table for asynchronous document processing tracking.

Revision ID: 002_add_ingestion_jobs_table
Revises: 001_initial_metadata_schema
Create Date: 2026-09-23 15:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_add_ingestion_jobs_table"
down_revision: Union[str, None] = "001_initial_metadata_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists (e.g. from create_tables)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "ingestion_jobs" not in tables:
        op.create_table(
            "ingestion_jobs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("document_id", sa.String(length=36), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
            sa.Column("stage", sa.String(length=50), nullable=False, server_default="queued"),
            sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_pages", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("processed_pages", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_chunks", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("processing_time_ms", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_ingestion_jobs_document_id"), "ingestion_jobs", ["document_id"], unique=False)
        op.create_index(op.f("ix_ingestion_jobs_status"), "ingestion_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingestion_jobs_status"), table_name="ingestion_jobs")
    op.drop_index(op.f("ix_ingestion_jobs_document_id"), table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
