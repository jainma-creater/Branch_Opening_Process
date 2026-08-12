"""add payments

Revision ID: 012_payments
Revises: 011_cc_approvals
"""

from alembic import op
import sqlalchemy as sa

revision = "012_payments"
down_revision = "011_cc_approvals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="RESTRICT")),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id", ondelete="RESTRICT")),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False, server_default="NEFT"),
        sa.Column("reference_no", sa.String(120)),
        sa.Column("payment_date", sa.Date()),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("remarks", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_payments_branch_opening_id", "payments", ["branch_opening_id"])
    op.create_index("ix_payments_status", "payments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_branch_opening_id", table_name="payments")
    op.drop_table("payments")
