from app.models.opening import WorkflowStage


def test_workflow_stage_order_is_fixed() -> None:
    assert list(WorkflowStage) == [
        WorkflowStage.REQUIREMENT,
        WorkflowStage.PROPERTY_SEARCH,
        WorkflowStage.PROPERTY_APPROVAL,
        WorkflowStage.SECURITY_DEPOSIT,
        WorkflowStage.LOA,
        WorkflowStage.AGREEMENT,
        WorkflowStage.QUOTATION,
        WorkflowStage.ACCOUNTS,
        WorkflowStage.CC_APPROVAL,
        WorkflowStage.MD_APPROVAL,
        WorkflowStage.PAYMENT,
        WorkflowStage.INFRASTRUCTURE,
        WorkflowStage.OPERATIONAL_READINESS,
        WorkflowStage.OPENING,
        WorkflowStage.COMPLETED,
    ]
