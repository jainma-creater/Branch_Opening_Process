"""create branch opening foundation

Revision ID: 001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("rent_limit", sa.Numeric(12, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_regions_name"),
    )
    op.create_index("ix_regions_name", "regions", ["name"], unique=False)

    op.create_table(
        "areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("rent_limit", sa.Numeric(12, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("region_id", "name", name="uq_area_region_name"),
    )
    op.create_index("ix_areas_region_id", "areas", ["region_id"])
    op.create_index("ix_areas_name", "areas", ["name"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("regions.id", ondelete="RESTRICT")),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("areas.id", ondelete="RESTRICT")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("employee_code", name="uq_users_employee_code"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_employee_code", "users", ["employee_code"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index("ix_users_region_id", "users", ["region_id"])
    op.create_index("ix_users_area_id", "users", ["area_id"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("branch_code", sa.String(50), nullable=False),
        sa.Column("rent_limit", sa.Numeric(12, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("branch_code", name="uq_branches_branch_code"),
    )
    op.create_index("ix_branches_area_id", "branches", ["area_id"])
    op.create_index("ix_branches_name", "branches", ["name"])
    op.create_index("ix_branches_branch_code", "branches", ["branch_code"])

    op.create_table(
        "branch_openings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opening_number", sa.String(30), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_type", sa.String(30), nullable=False),
        sa.Column("business_reason", sa.String(500)),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("requested_date", sa.Date(), nullable=False),
        sa.Column("tentative_operations_date", sa.Date()),
        sa.Column("agreement_commencement_date", sa.Date()),
        sa.Column("actual_opening_date", sa.Date()),
        sa.Column("current_stage", sa.String(40), nullable=False, server_default="REQUIREMENT"),
        sa.Column("case_status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("opening_number", name="uq_branch_openings_opening_number"),
    )
    op.create_index("ix_branch_openings_opening_number", "branch_openings", ["opening_number"])
    op.create_index("ix_branch_openings_branch_id", "branch_openings", ["branch_id"])
    op.create_index("ix_branch_openings_requested_by", "branch_openings", ["requested_by"])
    op.create_index("ix_branch_openings_current_stage", "branch_openings", ["current_stage"])
    op.create_index("ix_branch_openings_case_status", "branch_openings", ["case_status"])

    op.create_table(
        "workflow_stage_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.UniqueConstraint("code", name="uq_workflow_stage_definitions_code"),
    )
    op.create_index("ix_workflow_stage_definitions_code", "workflow_stage_definitions", ["code"])
    op.create_index("ix_workflow_stage_definitions_sequence", "workflow_stage_definitions", ["sequence"])

    op.create_table(
        "workflow_instances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opening_id", sa.Integer(), sa.ForeignKey("branch_openings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage_id", sa.Integer(), sa.ForeignKey("workflow_stage_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workflow_instances_opening_id", "workflow_instances", ["opening_id"])
    op.create_index("ix_workflow_instances_stage_id", "workflow_instances", ["stage_id"])
    op.create_index("ix_workflow_instances_status", "workflow_instances", ["status"])
    op.create_index("ix_workflow_instances_assigned_to", "workflow_instances", ["assigned_to"])
    op.create_index("ix_workflow_opening_stage", "workflow_instances", ["opening_id", "stage_id"])

    stages = [
        ("REQUIREMENT", "Branch Requirement", 1),
        ("PROPERTY_SEARCH", "Location / Property Search", 2),
        ("PROPERTY_APPROVAL", "Property Approval", 3),
        ("SECURITY_DEPOSIT", "Security Deposit Approval", 4),
        ("LOA", "LOA Request / Issuance", 5),
        ("AGREEMENT", "Agreement Preparation / Execution", 6),
        ("QUOTATION", "Three Quotations", 7),
        ("ACCOUNTS", "Accounts Review", 8),
        ("CC_APPROVAL", "CC Approval", 9),
        ("MD_APPROVAL", "MD Approval", 10),
        ("PAYMENT", "Payment", 11),
        ("INFRASTRUCTURE", "Infrastructure / Fit-out", 12),
        ("OPERATIONAL_READINESS", "Operational Readiness", 13),
        ("OPENING", "Branch Opening", 14),
        ("COMPLETED", "Completed", 15),
    ]
    op.bulk_insert(
        sa.table(
            "workflow_stage_definitions",
            sa.column("code", sa.String()),
            sa.column("name", sa.String()),
            sa.column("sequence", sa.Integer()),
        ),
        [{"code": code, "name": name, "sequence": sequence} for code, name, sequence in stages],
    )


def downgrade() -> None:
    op.drop_index("ix_workflow_opening_stage", table_name="workflow_instances")
    op.drop_index("ix_workflow_instances_assigned_to", table_name="workflow_instances")
    op.drop_index("ix_workflow_instances_status", table_name="workflow_instances")
    op.drop_index("ix_workflow_instances_stage_id", table_name="workflow_instances")
    op.drop_index("ix_workflow_instances_opening_id", table_name="workflow_instances")
    op.drop_table("workflow_instances")
    op.drop_index("ix_workflow_stage_definitions_sequence", table_name="workflow_stage_definitions")
    op.drop_index("ix_workflow_stage_definitions_code", table_name="workflow_stage_definitions")
    op.drop_table("workflow_stage_definitions")
    op.drop_index("ix_branch_openings_case_status", table_name="branch_openings")
    op.drop_index("ix_branch_openings_current_stage", table_name="branch_openings")
    op.drop_index("ix_branch_openings_requested_by", table_name="branch_openings")
    op.drop_index("ix_branch_openings_branch_id", table_name="branch_openings")
    op.drop_index("ix_branch_openings_opening_number", table_name="branch_openings")
    op.drop_table("branch_openings")
    op.drop_index("ix_branches_branch_code", table_name="branches")
    op.drop_index("ix_branches_name", table_name="branches")
    op.drop_index("ix_branches_area_id", table_name="branches")
    op.drop_table("branches")
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_area_id", table_name="users")
    op.drop_index("ix_users_region_id", table_name="users")
    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_employee_code", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_areas_name", table_name="areas")
    op.drop_index("ix_areas_region_id", table_name="areas")
    op.drop_table("areas")
    op.drop_index("ix_regions_name", table_name="regions")
    op.drop_table("regions")
