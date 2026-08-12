from conftest import ensure_user, login, org_structure


def _create_opening(client, structure: dict, headers: dict) -> dict:
    response = client.post(
        "/api/v1/openings",
        json={
            "branch_id": structure["branch_id"],
            "project_type": "NEW_BRANCH",
            "business_reason": "expansion",
            "requested_date": "2026-08-11",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _advance(client, opening_id: int, target: str, headers: dict) -> dict:
    return client.post(
        f"/api/v1/workflow/openings/{opening_id}/transition",
        json={"target_stage": target, "comments": "proceed"},
        headers=headers,
    )


def test_valid_transition_generates_tasks(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    response = _advance(client, opening["id"], "PROPERTY_SEARCH", headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["current_stage"] == "PROPERTY_SEARCH"

    tasks = client.get(
        f"/api/v1/workflow/openings/{opening['id']}/tasks", headers=headers
    ).json()
    stage_tasks = [t for t in tasks if t["stage"] == "PROPERTY_SEARCH"]
    assert len(stage_tasks) == 1
    assert stage_tasks[0]["task_type"] == "PROPERTY_SEARCH"

    completed_codes = [i["code"] for i in body["completed_stages"]]
    assert "REQUIREMENT" in completed_codes
    assert "PROPERTY_SEARCH" not in completed_codes
    assert len(body["pending_stages"]) == 14


def test_invalid_transition_conflict(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    response = _advance(client, opening["id"], "MD_APPROVAL", headers)
    assert response.status_code == 409


def test_sequential_journey_runs_full_path(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    path = [
        "PROPERTY_SEARCH",
        "PROPERTY_APPROVAL",
        "SECURITY_DEPOSIT",
        "LOA",
        "AGREEMENT",
        "QUOTATION",
        "ACCOUNTS",
        "CC_APPROVAL",
        "MD_APPROVAL",
        "PAYMENT",
        "INFRASTRUCTURE",
        "OPERATIONAL_READINESS",
        "OPENING",
        "COMPLETED",
    ]
    for target in path:
        response = _advance(client, opening["id"], target, headers)
        assert response.status_code == 200, (target, response.text)
        assert response.json()["current_stage"] == target

    final = client.get(f"/api/v1/openings/{opening['id']}", headers=headers).json()
    assert final["case_status"] == "COMPLETED"
    assert final["completed_at"] is not None
    assert len(final["completed_stages"]) == 15


def test_unauthorized_role_cannot_advance(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    ensure_user("BUSINESS_TEAM", "bt_advance")
    token = login(client, "bt_advance@example.com")
    response = _advance(
        client,
        opening["id"],
        "PROPERTY_SEARCH",
        {"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_accounts_navigates_forward_and_back_to_quotation(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    for target in ["PROPERTY_SEARCH", "PROPERTY_APPROVAL", "SECURITY_DEPOSIT", "LOA", "AGREEMENT", "QUOTATION", "ACCOUNTS"]:
        response = _advance(client, opening["id"], target, headers)
        assert response.status_code == 200, response.text

    ensure_user("ACCOUNTS", "acc1")
    acc_token = login(client, "acc1@example.com")
    acc_headers = {"Authorization": f"Bearer {acc_token}"}

    back = _advance(client, opening["id"], "QUOTATION", acc_headers)
    assert back.status_code == 200
    assert back.json()["current_stage"] == "QUOTATION"

    resubmit = _advance(client, opening["id"], "ACCOUNTS", headers)
    assert resubmit.status_code == 200
    assert resubmit.json()["current_stage"] == "ACCOUNTS"

    to_cc = _advance(client, opening["id"], "CC_APPROVAL", acc_headers)
    assert to_cc.status_code == 200


def test_send_back_to_previous_stage(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    for target in ["PROPERTY_SEARCH", "PROPERTY_APPROVAL", "SECURITY_DEPOSIT"]:
        _advance(client, opening["id"], target, headers)

    sent = client.post(
        f"/api/v1/workflow/openings/{opening['id']}/send-back",
        json={"comments": "relocate property"},
        headers=headers,
    )
    assert sent.status_code == 200, sent.text
    assert sent.json()["current_stage"] == "PROPERTY_APPROVAL"


def test_send_back_at_requirement_conflict(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    response = client.post(
        f"/api/v1/workflow/openings/{opening['id']}/send-back",
        json={},
        headers=headers,
    )
    assert response.status_code == 409


def test_completed_stage_has_no_targets(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    path = ["PROPERTY_SEARCH", "PROPERTY_APPROVAL", "SECURITY_DEPOSIT", "LOA", "AGREEMENT", "QUOTATION", "ACCOUNTS", "CC_APPROVAL", "MD_APPROVAL", "PAYMENT", "INFRASTRUCTURE", "OPERATIONAL_READINESS", "OPENING", "COMPLETED"]
    for target in path:
        _advance(client, opening["id"], target, headers)

    targets = client.get(
        f"/api/v1/workflow/openings/{opening['id']}/targets", headers=headers
    ).json()
    assert targets["targets"] == []

    conflict = _advance(client, opening["id"], "OPENING", headers)
    assert conflict.status_code == 409


def test_approval_request_and_decision(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    created = client.post(
        "/api/v1/approvals",
        params={"opening_id": opening["id"]},
        json={
            "entity_type": "property_options",
            "entity_id": "42",
            "approval_type": "PROPERTY",
            "amount": 14000,
            "comments": "approve property",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    approval = created.json()
    assert approval["decision"] is None
    assert approval["approval_type"] == "PROPERTY"

    decided = client.post(
        f"/api/v1/approvals/{approval['id']}/decision",
        json={"decision": "APPROVED", "comments": "ok", "amount": 14000},
        headers=headers,
    )
    assert decided.status_code == 200
    assert decided.json()["decision"] == "APPROVED"
    assert decided.json()["approver"] is not None
    assert decided.json()["decision_at"] is not None


def test_approval_decision_immutable(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    created = client.post(
        "/api/v1/approvals",
        params={"opening_id": opening["id"]},
        json={"entity_type": "x", "approval_type": "CC"},
        headers=headers,
    ).json()

    client.post(
        f"/api/v1/approvals/{created['id']}/decision",
        json={"decision": "APPROVED"},
        headers=headers,
    )
    second = client.post(
        f"/api/v1/approvals/{created['id']}/decision",
        json={"decision": "REJECTED"},
        headers=headers,
    )
    assert second.status_code == 409


def test_approval_reject_and_send_back_decisions(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)

    for decision in ("REJECTED", "SENT_BACK"):
        created = client.post(
            "/api/v1/approvals",
            params={"opening_id": opening["id"]},
            json={"entity_type": "x", "approval_type": "MD"},
            headers=headers,
        ).json()
        decided = client.post(
            f"/api/v1/approvals/{created['id']}/decision",
            json={"decision": decision, "comments": "review"},
            headers=headers,
        )
        assert decided.status_code == 200
        assert decided.json()["decision"] == decision


def test_task_lifecycle(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)
    _advance(client, opening["id"], "PROPERTY_SEARCH", headers)

    tasks = client.get(
        f"/api/v1/workflow/openings/{opening['id']}/tasks", headers=headers
    ).json()
    task = next(t for t in tasks if t["stage"] == "PROPERTY_SEARCH")

    started = client.post(
        f"/api/v1/workflow/tasks/{task['id']}/start", headers=headers
    )
    assert started.json()["status"] == "IN_PROGRESS"

    completed = client.post(
        f"/api/v1/workflow/tasks/{task['id']}/complete",
        json={"remarks": "property verified"},
        headers=headers,
    )
    assert completed.status_code == 200
    body = completed.json()
    assert body["status"] == "COMPLETED"
    assert body["remarks"] == "property verified"
    assert body["completed_by"] is not None


def test_my_tasks_endpoint(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create_opening(client, structure, headers)
    _advance(client, opening["id"], "PROPERTY_SEARCH", headers)

    mine = client.get("/api/v1/workflow/tasks/my", headers=headers)
    assert mine.status_code == 200
    assert len(mine.json()) >= 1