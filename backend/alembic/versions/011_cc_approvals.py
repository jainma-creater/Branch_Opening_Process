"""add cc requests and items

Revision ID: 011_cc_approvals
Revises: 010_accounts_invoices
"""

from alembic import op
import sqlalchemy as sa

revision = "011_cc_approvals"
down_revision = "010_accounts_invoices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cc_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_code", sa.String(60), nullable=True, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("cc_reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("md_reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("remarks", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cc_requests_status", "cc_requests", ["status"])
    op.create_index("ix_cc_requests_request_code", "cc_requests", ["request_code"])

    op.create_table(
        "cc_request_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "cc_request_id",
            sa.Integer(),
            sa.ForeignKey("cc_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("requested_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("approved_amount", sa.Numeric(14, 2)),
        sa.Column("remarks", sa.String(500)),
    )
    op.create_index("ix_cc_request_items_cc_request_id", "cc_request_items", ["cc_request_id"])
    op.create_index("ix_cc_request_items_branch_opening_id", "cc_request_items", ["branch_opening_id"])


def downgrade() -> None:
    op.drop_index("ix_cc_request_items_branch_opening_id", table_name="cc_request_items")
    op.drop_index("ix_cc_request_items_cc_request_id", table_name="cc_request_items")
    op.drop_table("cc_request_items")
    op.drop_index("ix_cc_requests_request_code", table_name="cc_requests")
    op.drop_index("ix_cc_requests_status", table_name="cc_requests")
    op.drop_table("cc_requests")
