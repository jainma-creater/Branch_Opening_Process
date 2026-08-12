from conftest import org_structure


def _open(client, structure, headers, branch_id=None) -> dict:
    response = client.post(
        "/api/v1/openings",
        json={
            "branch_id": branch_id or structure["branch_id"],
            "project_type": "NEW_BRANCH",
            "business_reason": "expansion",
            "requested_date": "2026-08-11",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_summary_counts(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    _open(client, structure, headers)
    _open(client, structure, headers)

    summary = client.get("/api/v1/reports/summary", headers=headers).json()
    assert summary["total_openings"] == 2
    assert summary["completed_openings"] == 0
    assert summary["openings_by_stage"]["REQUIREMENT"] == 2


def test_pending_approvals_lists_openings(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    # create a pending APPROVAL of type ACCOUNTS for this opening
    created = client.post(
        "/api/v1/approvals",
        params={"opening_id": opening["id"]},
        json={"entity_type": "quotation_requests", "approval_type": "ACCOUNTS"},
        headers=headers,
    )
    assert created.status_code == 201, created.text

    pending = client.get("/api/v1/reports/pending-approvals", headers=headers).json()
    assert any(p["opening_id"] == opening["id"] for p in pending)
    match = next(p for p in pending if p["opening_id"] == opening["id"])
    assert "ACCOUNTS" in match["pending_approval_types"]
    assert match["opening_number"] == opening["opening_number"]


def test_spend_totals(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    vendor = client.post(
        "/api/v1/procurement/vendors",
        json={"name": "M/s Report", "contact_person": "K"},
        headers=headers,
    ).json()

    inv = client.post(
        f"/api/v1/accounts/openings/{opening['id']}/invoices",
        json={"vendor_id": vendor["id"], "invoice_number": "INV-R1", "amount": 1000, "tax": 100},
        headers=headers,
    ).json()
    # approve the invoice so it counts as approved spend
    client.post(f"/api/v1/accounts/invoices/{inv['id']}/submit", headers=headers)
    ensure_accounts(client)
    acc_token = login_accounts(client)
    client.post(
        f"/api/v1/accounts/invoices/{inv['id']}/review",
        json={"decision": "APPROVED"},
        headers={"Authorization": f"Bearer {acc_token}"},
    )

    spend = client.get("/api/v1/reports/spend", headers=headers).json()
    assert spend["total_invoiced"] == 1100.0
    assert spend["approved_invoiced"] == 1100.0


def ensure_accounts(client):
    from conftest import ensure_user

    ensure_user("ACCOUNTS", "acc_report")


def login_accounts(client):
    from conftest import login

    return login(client, "acc_report@example.com")
