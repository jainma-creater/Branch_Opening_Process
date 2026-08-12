from conftest import _test_session, ensure_user, login, org_structure


def _accounts_token(client: object) -> str:
    ensure_user("ACCOUNTS", "accounts_user")
    return login(client, "accounts_user@example.com")


def _set_stage(opening_id: int, stage: str) -> None:
    session = _test_session()
    try:
        from app.models import BranchOpening

        opening = session.get(BranchOpening, opening_id)
        opening.current_stage = stage
        session.commit()
    finally:
        session.close()


def _make_quotation_request(opening_id: int) -> int:
    session = _test_session()
    try:
        from app.models import QuotationRequest

        request = QuotationRequest(
            branch_opening_id=opening_id, scope_description="Fit-out", status="OPEN"
        )
        session.add(request)
        session.commit()
        session.refresh(request)
        return request.id
    finally:
        session.close()


def _opening_stage(opening_id: int) -> str:
    session = _test_session()
    try:
        from app.models import BranchOpening

        return session.get(BranchOpening, opening_id).current_stage
    finally:
        session.close()


def _request_approved_amount(request_id: int):
    session = _test_session()
    try:
        from app.models import QuotationRequest

        return session.get(QuotationRequest, request_id).approved_amount
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
        json={"name": "M/s Furniture Co", "contact_person": "Ramesh"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()


def test_quotation_approval_sets_amount_and_advances(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "ACCOUNTS")
    request_id = _make_quotation_request(opening["id"])

    token = _accounts_token(client)
    response = client.post(
        f"/api/v1/accounts/openings/{opening['id']}/quotation-requests/{request_id}/review",
        json={"decision": "APPROVED", "approved_amount": 50000, "comments": "ok"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert float(_request_approved_amount(request_id)) == 50000.0
    assert _opening_stage(opening["id"]) == "CC_APPROVAL"


def test_quotation_send_back_to_quotation(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "ACCOUNTS")
    request_id = _make_quotation_request(opening["id"])

    token = _accounts_token(client)
    response = client.post(
        f"/api/v1/accounts/openings/{opening['id']}/quotation-requests/{request_id}/review",
        json={"decision": "SENT_BACK", "comments": "renegotiate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert _opening_stage(opening["id"]) == "QUOTATION"


def test_invoice_total_calculation(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendor = _vendor(client, headers)

    response = client.post(
        f"/api/v1/accounts/openings/{opening['id']}/invoices",
        json={
            "vendor_id": vendor["id"],
            "invoice_number": "INV-001",
            "amount": 1000,
            "tax": 180,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert float(body["total_amount"]) == 1180.0
    assert body["version"] == 1
    assert body["status"] == "DRAFT"


def test_invoice_review_approved(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendor = _vendor(client, headers)
    created = client.post(
        f"/api/v1/accounts/openings/{opening['id']}/invoices",
        json={"vendor_id": vendor["id"], "invoice_number": "INV-002", "amount": 500, "tax": 90},
        headers=headers,
    ).json()
    invoice_id = created["id"]

    submit = client.post(
        f"/api/v1/accounts/invoices/{invoice_id}/submit", headers=headers
    )
    assert submit.status_code == 200, submit.text

    token = _accounts_token(client)
    review = client.post(
        f"/api/v1/accounts/invoices/{invoice_id}/review",
        json={"decision": "APPROVED", "remarks": "verified"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert review.status_code == 200, review.text
    assert review.json()["status"] == "APPROVED"


def test_invoice_mismatch_then_revise_history(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendor = _vendor(client, headers)
    created = client.post(
        f"/api/v1/accounts/openings/{opening['id']}/invoices",
        json={"vendor_id": vendor["id"], "invoice_number": "INV-003", "amount": 700, "tax": 70},
        headers=headers,
    ).json()
    invoice_id = created["id"]

    client.post(f"/api/v1/accounts/invoices/{invoice_id}/submit", headers=headers)

    token = _accounts_token(client)
    mismatch = client.post(
        f"/api/v1/accounts/invoices/{invoice_id}/review",
        json={"decision": "MISMATCH", "remarks": "amount differs"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert mismatch.status_code == 200, mismatch.text
    assert mismatch.json()["status"] == "MISMATCH"

    revised = client.post(
        f"/api/v1/accounts/invoices/{invoice_id}/revise",
        json={"invoice_number": "INV-003R", "amount": 650, "tax": 65},
        headers=headers,
    )
    assert revised.status_code == 201, revised.text
    body = revised.json()
    assert body["version"] == 2
    assert body["parent_invoice_id"] == invoice_id
    assert body["status"] == "REVISED"
    assert float(body["total_amount"]) == 715.0

    history = client.get(
        f"/api/v1/accounts/invoices/{invoice_id}/history", headers=headers
    )
    assert history.status_code == 200, history.text
    assert len(history.json()) == 2


def test_invoice_double_review_guard(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendor = _vendor(client, headers)
    created = client.post(
        f"/api/v1/accounts/openings/{opening['id']}/invoices",
        json={"vendor_id": vendor["id"], "invoice_number": "INV-004", "amount": 300, "tax": 30},
        headers=headers,
    ).json()
    invoice_id = created["id"]
    client.post(f"/api/v1/accounts/invoices/{invoice_id}/submit", headers=headers)

    token = _accounts_token(client)
    first = client.post(
        f"/api/v1/accounts/invoices/{invoice_id}/review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/api/v1/accounts/invoices/{invoice_id}/review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second.status_code == 409
