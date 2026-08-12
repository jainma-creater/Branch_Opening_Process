"""add procurement: vendors, quotation requests, quotations

Revision ID: 009_procurement
Revises: 008_agreements
"""
from alembic import op
import sqlalchemy as sa

revision = "009_procurement"
down_revision = "008_agreements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("contact_person", sa.String(120)),
        sa.Column("phone", sa.String(30)),
        sa.Column("email", sa.String(255)),
        sa.Column("address", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vendors_name", "vendors", ["name"])

    op.create_table(
        "quotation_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_date", sa.Date()),
        sa.Column("required_date", sa.Date()),
        sa.Column("scope_description", sa.String(1000)),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("selected_vendor_id", sa.Integer(), sa.ForeignKey("vendors.id", ondelete="RESTRICT")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_quotation_requests_branch_opening_id", "quotation_requests", ["branch_opening_id"])

    op.create_table(
        "quotation_request_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "request_id",
            sa.Integer(),
            sa.ForeignKey("quotation_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(30)),
    )
    op.create_index("ix_quotation_request_items_request_id", "quotation_request_items", ["request_id"])

    op.create_table(
        "quotations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "request_id",
            sa.Integer(),
            sa.ForeignKey("quotation_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vendor_id",
            sa.Integer(),
            sa.ForeignKey("vendors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quotation_date", sa.Date()),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="SUBMITTED"),
        sa.Column("remarks", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("request_id", "vendor_id", name="uq_quotation_request_vendor"),
    )
    op.create_index("ix_quotations_request_id", "quotations", ["request_id"])
    op.create_index("ix_quotations_vendor_id", "quotations", ["vendor_id"])

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "quotation_id",
            sa.Integer(),
            sa.ForeignKey("quotations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(30)),
        sa.Column("rate", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("tax", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("final_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
    )
    op.create_index("ix_quotation_items_quotation_id", "quotation_items", ["quotation_id"])


def downgrade() -> None:
    op.drop_index("ix_quotation_items_quotation_id", table_name="quotation_items")
    op.drop_table("quotation_items")
    op.drop_index("ix_quotations_vendor_id", table_name="quotations")
    op.drop_index("ix_quotations_request_id", table_name="quotations")
    op.drop_table("quotations")
    op.drop_index("ix_quotation_request_items_request_id", table_name="quotation_request_items")
    op.drop_table("quotation_request_items")
    op.drop_index("ix_quotation_requests_branch_opening_id", table_name="quotation_requests")
    op.drop_table("quotation_requests")
    op.drop_index("ix_vendors_name", table_name="vendors")
    op.drop_table("vendors")