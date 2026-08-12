"""add branch opening assignment

Revision ID: 004_opening_assignment
Revises: 003_users_auth_roles
"""
from alembic import op
import sqlalchemy as sa

revision = "004_opening_assignment"
down_revision = "003_users_auth_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "branch_openings",
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
    )
    op.create_index("ix_branch_openings_assigned_to", "branch_openings", ["assigned_to"])


def downgrade() -> None:
    op.drop_index("ix_branch_openings_assigned_to", table_name="branch_openings")
    op.drop_column("branch_openings", "assigned_to")