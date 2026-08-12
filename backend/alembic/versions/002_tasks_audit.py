"""add workflow tasks and audit events

Revision ID: 002_tasks_audit
Revises: 001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "002_tasks_audit"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("task_type", sa.String(80), nullable=False),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("completed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("remarks", sa.Text()),
    )
    op.create_index("ix_workflow_tasks_branch_opening_id", "workflow_tasks", ["branch_opening_id"])
    op.create_index("ix_workflow_tasks_stage", "workflow_tasks", ["stage"])
    op.create_index("ix_workflow_tasks_status", "workflow_tasks", ["status"])
    op.create_index("ix_workflow_tasks_assigned_to", "workflow_tasks", ["assigned_to"])
    op.create_index("ix_workflow_tasks_opening_status", "workflow_tasks", ["branch_opening_id", "status"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_opening_id",
            sa.Integer(),
            sa.ForeignKey("branch_openings.id", ondelete="SET NULL"),
        ),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("entity_id", sa.String(64)),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("stage", sa.String(40)),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("comments", sa.Text()),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_branch_opening_id", "audit_events", ["branch_opening_id"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_stage", "audit_events", ["stage"])
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_opening_timestamp", "audit_events", ["branch_opening_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_opening_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_user_id", table_name="audit_events")
    op.drop_index("ix_audit_events_stage", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_id", table_name="audit_events")
    op.drop_index("ix_audit_events_branch_opening_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_workflow_tasks_opening_status", table_name="workflow_tasks")
    op.drop_index("ix_workflow_tasks_assigned_to", table_name="workflow_tasks")
    op.drop_index("ix_workflow_tasks_status", table_name="workflow_tasks")
    op.drop_index("ix_workflow_tasks_stage", table_name="workflow_tasks")
    op.drop_index("ix_workflow_tasks_branch_opening_id", table_name="workflow_tasks")
    op.drop_table("workflow_tasks")