"""add approvals

Revision ID: 005_approvals
Revises: 004_opening_assignment
"""
from alembic import op
import sqlalchemy as sa

revision = "005_approvals"
down_revision = "004_opening_assignment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("entity_id", sa.String(64)),
        sa.Column("approval_type", sa.String(40), nullable=False),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("approver", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("decision", sa.String(20)),
        sa.Column("decision_at", sa.DateTime(timezone=True)),
        sa.Column("comments", sa.Text()),
        sa.Column("amount", sa.Numeric(14, 2)),
    )
    op.create_index("ix_approvals_branch_opening_id", "approvals", ["branch_opening_id"])
    op.create_index("ix_approvals_entity_id", "approvals", ["entity_id"])
    op.create_index("ix_approvals_approval_type", "approvals", ["approval_type"])
    op.create_index("ix_approvals_approver", "approvals", ["approver"])
    op.create_index("ix_approvals_decision", "approvals", ["decision"])
    op.create_index("ix_approvals_opening_type", "approvals", ["branch_opening_id", "approval_type"])


def downgrade() -> None:
    op.drop_index("ix_approvals_opening_type", table_name="approvals")
    op.drop_index("ix_approvals_decision", table_name="approvals")
    op.drop_index("ix_approvals_approver", table_name="approvals")
    op.drop_index("ix_approvals_approval_type", table_name="approvals")
    op.drop_index("ix_approvals_entity_id", table_name="approvals")
    op.drop_index("ix_approvals_branch_opening_id", table_name="approvals")
    op.drop_table("approvals")