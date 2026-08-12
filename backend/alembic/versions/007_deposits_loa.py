"""add security deposits and loa

Revision ID: 007_deposits_loa
Revises: 006_properties
"""
from alembic import op
import sqlalchemy as sa

revision = "007_deposits_loa"
down_revision = "006_properties"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "security_deposits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("remarks", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_security_deposits_branch_opening_id", "security_deposits", ["branch_opening_id"])

    op.create_table(
        "deposit_payees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "deposit_id",
            sa.Integer(),
            sa.ForeignKey("security_deposits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("remarks", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deposit_payees_deposit_id", "deposit_payees", ["deposit_id"])

    op.create_table(
        "deposit_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "payee_id",
            sa.Integer(),
            sa.ForeignKey("deposit_payees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_date", sa.Date()),
        sa.Column("reference", sa.String(120)),
        sa.Column("status", sa.String(20), nullable=False, server_default="PAID"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deposit_payments_payee_id", "deposit_payments", ["payee_id"])

    op.create_table(
        "loa_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("employee", sa.String(200), nullable=False),
        sa.Column("employee_code", sa.String(50), nullable=False),
        sa.Column("request_date", sa.Date()),
        sa.Column("execution_date", sa.Date()),
        sa.Column("agreement_tenure", sa.String(120)),
        sa.Column("issued_date", sa.Date()),
        sa.Column("status", sa.String(20), nullable=False, server_default="REQUESTED"),
        sa.Column("remarks", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_loa_requests_branch_opening_id", "loa_requests", ["branch_opening_id"])
    op.create_index("ix_loa_requests_status", "loa_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_loa_requests_status", table_name="loa_requests")
    op.drop_index("ix_loa_requests_branch_opening_id", table_name="loa_requests")
    op.drop_table("loa_requests")
    op.drop_index("ix_deposit_payments_payee_id", table_name="deposit_payments")
    op.drop_table("deposit_payments")
    op.drop_index("ix_deposit_payees_deposit_id", table_name="deposit_payees")
    op.drop_table("deposit_payees")
    op.drop_index("ix_security_deposits_branch_opening_id", table_name="security_deposits")
    op.drop_table("security_deposits")