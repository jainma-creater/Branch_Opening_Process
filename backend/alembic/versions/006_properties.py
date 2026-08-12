"""add property options

Revision ID: 006_properties
Revises: 005_approvals
"""
from alembic import op
import sqlalchemy as sa

revision = "006_properties"
down_revision = "005_approvals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "property_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("option_sequence", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("area_sqft", sa.Numeric(12, 2)),
        sa.Column("rent", sa.Numeric(14, 2)),
        sa.Column("deposit", sa.Numeric(14, 2)),
        sa.Column("annual_increment", sa.Numeric(6, 2)),
        sa.Column("entrance", sa.String(20)),
        sa.Column("restroom", sa.String(20)),
        sa.Column("possession_status", sa.String(40)),
        sa.Column("remarks", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="UNDER_REVIEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("branch_opening_id", "option_sequence", name="uq_property_option_sequence"),
    )
    op.create_index("ix_property_options_branch_opening_id", "property_options", ["branch_opening_id"])
    op.create_index("ix_property_options_status", "property_options", ["status"])


def downgrade() -> None:
    op.drop_index("ix_property_options_status", table_name="property_options")
    op.drop_index("ix_property_options_branch_opening_id", table_name="property_options")
    op.drop_table("property_options")