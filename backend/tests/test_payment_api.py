from conftest import _test_session, ensure_user, login, org_structure


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


def _vendor(client, headers) -> dict:
    created = client.post(
        "/api/v1/procurement/vendors",
        json={"name": "M/s Fitout", "contact_person": "Ravi"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()


def _invoice(client, opening_id, vendor_id, headers) -> dict:
    created = client.post(
        f"/api/v1/accounts/openings/{opening_id}/invoices",
        json={"vendor_id": vendor_id, "invoice_number": "INV-P1", "amount": 1000, "tax": 100},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()


def test_payment_create_and_submit(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "PAYMENT")
    vendor = _vendor(client, headers)
    invoice = _invoice(client, opening["id"], vendor["id"], headers)

    created = client.post(
        f"/api/v1/payments/openings/{opening['id']}",
        json={
            "invoice_id": invoice["id"],
            "vendor_id": vendor["id"],
            "amount": 1100,
            "mode": "NEFT",
            "reference_no": "NEFT123",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "DRAFT"
    assert float(body["amount"]) == 1100.0

    submitted = client.post(
        f"/api/v1/payments/{body['id']}/submit", headers=headers
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "SUBMITTED"


def test_payment_review_approved_then_paid_advances(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "PAYMENT")
    vendor = _vendor(client, headers)
    invoice = _invoice(client, opening["id"], vendor["id"], headers)

    created = client.post(
        f"/api/v1/payments/openings/{opening['id']}",
        json={"invoice_id": invoice["id"], "vendor_id": vendor["id"], "amount": 1100},
        headers=headers,
    ).json()
    payment_id = created["id"]
    client.post(f"/api/v1/payments/{payment_id}/submit", headers=headers)

    ensure_user("ACCOUNTS", "acc_pay")
    acc_token = login(client, "acc_pay@example.com")
    reviewed = client.post(
        f"/api/v1/payments/{payment_id}/review",
        json={"decision": "APPROVED", "comments": "verified"},
        headers={"Authorization": f"Bearer {acc_token}"},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "APPROVED"

    paid = client.post(
        f"/api/v1/payments/{payment_id}/mark-paid", headers=headers
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["status"] == "PAID"
    assert _opening_stage(opening["id"]) == "INFRASTRUCTURE"


def test_payment_rejected(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "PAYMENT")
    vendor = _vendor(client, headers)
    invoice = _invoice(client, opening["id"], vendor["id"], headers)

    created = client.post(
        f"/api/v1/payments/openings/{opening['id']}",
        json={"invoice_id": invoice["id"], "vendor_id": vendor["id"], "amount": 1100},
        headers=headers,
    ).json()
    payment_id = created["id"]
    client.post(f"/api/v1/payments/{payment_id}/submit", headers=headers)

    ensure_user("ACCOUNTS", "acc_pay2")
    acc_token = login(client, "acc_pay2@example.com")
    rejected = client.post(
        f"/api/v1/payments/{payment_id}/review",
        json={"decision": "REJECTED", "comments": "mismatch"},
        headers={"Authorization": f"Bearer {acc_token}"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "REJECTED"


def test_payment_double_review_guard(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "PAYMENT")
    vendor = _vendor(client, headers)
    invoice = _invoice(client, opening["id"], vendor["id"], headers)

    created = client.post(
        f"/api/v1/payments/openings/{opening['id']}",
        json={"invoice_id": invoice["id"], "vendor_id": vendor["id"], "amount": 1100},
        headers=headers,
    ).json()
    payment_id = created["id"]
    client.post(f"/api/v1/payments/{payment_id}/submit", headers=headers)

    ensure_user("ACCOUNTS", "acc_pay3")
    acc_token = login(client, "acc_pay3@example.com")
    first = client.post(
        f"/api/v1/payments/{payment_id}/review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {acc_token}"},
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/api/v1/payments/{payment_id}/review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {acc_token}"},
    )
    assert second.status_code == 409
