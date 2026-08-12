"""add user password auth and seed roles

Revision ID: 003_users_auth_roles
Revises: 002_tasks_audit
"""
from alembic import op
import sqlalchemy as sa

revision = "003_users_auth_roles"
down_revision = "002_tasks_audit"
branch_labels = None
depends_on = None

ROLES = [
    ("SUPER_ADMIN", "Platform super administrator"),
    ("ADMIN", "Case administrator"),
    ("BUSINESS_TEAM", "Business / requirements team"),
    ("REGIONAL_ADMIN", "Regional administrator"),
    ("SD", "Security deposit officer"),
    ("ACCOUNTS", "Accounts / finance"),
    ("CC", "Cost committee approver"),
    ("MD", "Managing director approver"),
]


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))

    roles_table = sa.table(
        "roles",
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
    )
    op.bulk_insert(roles_table, [{"name": n, "description": d} for n, d in ROLES])


def downgrade() -> None:
    op.drop_column("users", "password_hash")