"""add agreements

Revision ID: 008_agreements
Revises: 007_deposits_loa
"""
from alembic import op
import sqlalchemy as sa

revision = "008_agreements"
down_revision = "007_deposits_loa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agreements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agreement_date", sa.Date()),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("tenure", sa.String(120)),
        sa.Column("monthly_rent", sa.Numeric(14, 2)),
        sa.Column("annual_increment", sa.Numeric(6, 2)),
        sa.Column("security_deposit", sa.Numeric(14, 2)),
        sa.Column("lock_in", sa.String(120)),
        sa.Column("fitout_period", sa.String(120)),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("remarks", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agreements_branch_opening_id", "agreements", ["branch_opening_id"])
    op.create_index("ix_agreements_status", "agreements", ["status"])

    op.create_table(
        "agreement_parties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "agreement_id",
            sa.Integer(),
            sa.ForeignKey("agreements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("party_type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("details", sa.String(500)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(30)),
    )
    op.create_index("ix_agreement_parties_agreement_id", "agreement_parties", ["agreement_id"])


def downgrade() -> None:
    op.drop_index("ix_agreement_parties_agreement_id", table_name="agreement_parties")
    op.drop_table("agreement_parties")
    op.drop_index("ix_agreements_status", table_name="agreements")
    op.drop_index("ix_agreements_branch_opening_id", table_name="agreements")
    op.drop_table("agreements")