"""add accounts columns and invoices

Revision ID: 010_accounts_invoices
Revises: 009_procurement
"""
from alembic import op
import sqlalchemy as sa

revision = "010_accounts_invoices"
down_revision = "009_procurement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quotation_requests",
        sa.Column("approved_amount", sa.Numeric(14, 2)),
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vendor_id",
            sa.Integer(),
            sa.ForeignKey("vendors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("invoice_number", sa.String(60), nullable=False),
        sa.Column("invoice_date", sa.Date()),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="SET NULL")),
        sa.Column("remarks", sa.String(1000)),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invoices_branch_opening_id", "invoices", ["branch_opening_id"])
    op.create_index("ix_invoices_vendor_id", "invoices", ["vendor_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])


def downgrade() -> None:
    op.drop_index("ix_invoices_invoice_number", table_name="invoices")
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_vendor_id", table_name="invoices")
    op.drop_index("ix_invoices_branch_opening_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_column("quotation_requests", "approved_amount")