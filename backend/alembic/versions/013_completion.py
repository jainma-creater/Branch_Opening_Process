"""add completion stages: fitouts, readiness items, opening records

Revision ID: 013_completion
Revises: 012_payments
"""

from alembic import op
import sqlalchemy as sa

revision = "013_completion"
down_revision = "012_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fitouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id", ondelete="RESTRICT")),
        sa.Column("scope", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PLANNED"),
        sa.Column("start_date", sa.Date()),
        sa.Column("expected_end_date", sa.Date()),
        sa.Column("completion_date", sa.Date()),
        sa.Column("remarks", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fitouts_branch_opening_id", "fitouts", ["branch_opening_id"])
    op.create_index("ix_fitouts_status", "fitouts", ["status"])

    op.create_table(
        "readiness_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("remarks", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_readiness_items_branch_opening_id", "readiness_items", ["branch_opening_id"])

    op.create_table(
        "opening_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("opening_date", sa.Date()),
        sa.Column("inaugurated_by", sa.String(200)),
        sa.Column("remarks", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_opening_records_branch_opening_id", "opening_records", ["branch_opening_id"])


def downgrade() -> None:
    op.drop_index("ix_opening_records_branch_opening_id", table_name="opening_records")
    op.drop_table("opening_records")
    op.drop_index("ix_readiness_items_branch_opening_id", table_name="readiness_items")
    op.drop_table("readiness_items")
    op.drop_index("ix_fitouts_status", table_name="fitouts")
    op.drop_index("ix_fitouts_branch_opening_id", table_name="fitouts")
    op.drop_table("fitouts")
