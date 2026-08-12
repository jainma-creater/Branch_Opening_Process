from conftest import _test_session, ensure_user, login, org_structure


def _cc_token(client: object) -> str:
    ensure_user("CC", "cc_user")
    return login(client, "cc_user@example.com")


def _md_token(client: object) -> str:
    ensure_user("MD", "md_user")
    return login(client, "md_user@example.com")


def _set_stage(opening_id: int, stage: str) -> None:
    session = _test_session()
    try:
        from app.models import BranchOpening

        opening = session.get(BranchOpening, opening_id)
        opening.current_stage = stage
        session.commit()
    finally:
        session.close()


def _opening_stage(opening_id: int) -> str:
    session = _test_session()
    try:
        from app.models import BranchOpening

        return session.get(BranchOpening, opening_id).current_stage
    finally:
        session.close()


def _open(client, structure, headers) -> dict:
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


def test_cc_request_bundles_openings(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    o1 = _open(client, structure, headers)
    o2 = _open(client, structure, headers)

    created = client.post(
        "/api/v1/cc-approvals/requests",
        json={
            "remarks": "Q3 bundle",
            "items": [
                {"branch_opening_id": o1["id"], "requested_amount": 200000},
                {"branch_opening_id": o2["id"], "requested_amount": 150000},
            ],
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "DRAFT"
    assert body["request_code"].startswith("CC-")
    assert len(body["items"]) == 2


def test_cc_approve_then_md_approve_advances(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    o1 = _open(client, structure, headers)
    o2 = _open(client, structure, headers)
    _set_stage(o1["id"], "CC_APPROVAL")
    _set_stage(o2["id"], "CC_APPROVAL")

    created = client.post(
        "/api/v1/cc-approvals/requests",
        json={
            "items": [
                {"branch_opening_id": o1["id"], "requested_amount": 200000},
                {"branch_opening_id": o2["id"], "requested_amount": 150000},
            ]
        },
        headers=headers,
    ).json()
    request_id = created["id"]

    submitted = client.post(
        f"/api/v1/cc-approvals/requests/{request_id}/submit", headers=headers
    )
    assert submitted.status_code == 200, submitted.text

    cc_token = _cc_token(client)
    cc_review = client.post(
        f"/api/v1/cc-approvals/requests/{request_id}/cc-review",
        json={
            "decision": "APPROVED",
            "items": [
                {"branch_opening_id": o1["id"], "approved_amount": 195000},
                {"branch_opening_id": o2["id"], "approved_amount": 150000},
            ],
        },
        headers={"Authorization": f"Bearer {cc_token}"},
    )
    assert cc_review.status_code == 200, cc_review.text
    assert cc_review.json()["status"] == "CC_APPROVED"
    assert _opening_stage(o1["id"]) == "MD_APPROVAL"
    assert _opening_stage(o2["id"]) == "MD_APPROVAL"
    items = {i["branch_opening_id"]: i for i in cc_review.json()["items"]}
    assert float(items[o1["id"]]["approved_amount"]) == 195000.0

    md_token = _md_token(client)
    md_review = client.post(
        f"/api/v1/cc-approvals/requests/{request_id}/md-review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {md_token}"},
    )
    assert md_review.status_code == 200, md_review.text
    assert md_review.json()["status"] == "MD_APPROVED"
    assert _opening_stage(o1["id"]) == "PAYMENT"
    assert _opening_stage(o2["id"]) == "PAYMENT"


def test_cc_send_back_to_accounts(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    o1 = _open(client, structure, headers)
    _set_stage(o1["id"], "CC_APPROVAL")

    created = client.post(
        "/api/v1/cc-approvals/requests",
        json={"items": [{"branch_opening_id": o1["id"], "requested_amount": 100000}]},
        headers=headers,
    ).json()
    request_id = created["id"]
    client.post(f"/api/v1/cc-approvals/requests/{request_id}/submit", headers=headers)

    cc_token = _cc_token(client)
    sent = client.post(
        f"/api/v1/cc-approvals/requests/{request_id}/cc-review",
        json={"decision": "SENT_BACK", "comments": "revise quote"},
        headers={"Authorization": f"Bearer {cc_token}"},
    )
    assert sent.status_code == 200, sent.text
    assert sent.json()["status"] == "SENT_BACK"
    assert _opening_stage(o1["id"]) == "ACCOUNTS"


def test_md_send_back_to_cc(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    o1 = _open(client, structure, headers)
    _set_stage(o1["id"], "CC_APPROVAL")

    created = client.post(
        "/api/v1/cc-approvals/requests",
        json={"items": [{"branch_opening_id": o1["id"], "requested_amount": 100000}]},
        headers=headers,
    ).json()
    request_id = created["id"]
    client.post(f"/api/v1/cc-approvals/requests/{request_id}/submit", headers=headers)

    cc_token = _cc_token(client)
    client.post(
        f"/api/v1/cc-approvals/requests/{request_id}/cc-review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {cc_token}"},
    )
    assert _opening_stage(o1["id"]) == "MD_APPROVAL"

    md_token = _md_token(client)
    sent = client.post(
        f"/api/v1/cc-approvals/requests/{request_id}/md-review",
        json={"decision": "SENT_BACK", "comments": "more detail"},
        headers={"Authorization": f"Bearer {md_token}"},
    )
    assert sent.status_code == 200, sent.text
    assert sent.json()["status"] == "SENT_BACK"
    assert _opening_stage(o1["id"]) == "CC_APPROVAL"


def test_cc_double_review_guard(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    o1 = _open(client, structure, headers)
    _set_stage(o1["id"], "CC_APPROVAL")

    created = client.post(
        "/api/v1/cc-approvals/requests",
        json={"items": [{"branch_opening_id": o1["id"], "requested_amount": 100000}]},
        headers=headers,
    ).json()
    request_id = created["id"]
    client.post(f"/api/v1/cc-approvals/requests/{request_id}/submit", headers=headers)

    cc_token = _cc_token(client)
    first = client.post(
        f"/api/v1/cc-approvals/requests/{request_id}/cc-review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {cc_token}"},
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/api/v1/cc-approvals/requests/{request_id}/cc-review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {cc_token}"},
    )
    assert second.status_code == 409
