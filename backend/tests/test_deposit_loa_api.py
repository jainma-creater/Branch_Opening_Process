from conftest import org_structure


def _open(client, structure: dict, headers: dict) -> dict:
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


def test_deposit_with_multiple_payees(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    deposit = client.post(
        f"/api/v1/deposits/openings/{opening['id']}",
        json={"total_amount": 42000},
        headers=headers,
    )
    assert deposit.status_code == 201, deposit.text
    deposit_id = deposit.json()["id"]

    payee1 = client.post(
        f"/api/v1/deposits/{deposit_id}/payees",
        json={"name": "Landlord 1", "amount": 21000},
        headers=headers,
    )
    payee2 = client.post(
        f"/api/v1/deposits/{deposit_id}/payees",
        json={"name": "Landlord 2", "amount": 21000},
        headers=headers,
    )
    assert payee1.status_code == 201
    assert payee2.status_code == 201

    detail = client.get(f"/api/v1/deposits/{deposit_id}", headers=headers).json()
    assert len(detail["payees"]) == 2
    assert detail["status"] == "PENDING"
    assert detail["paid_amount"] == 0


def test_payee_allocation_cannot_exceed_total(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    deposit_id = client.post(
        f"/api/v1/deposits/openings/{opening['id']}",
        json={"total_amount": 42000},
        headers=headers,
    ).json()["id"]

    client.post(
        f"/api/v1/deposits/{deposit_id}/payees",
        json={"name": "L1", "amount": 30000},
        headers=headers,
    )
    over = client.post(
        f"/api/v1/deposits/{deposit_id}/payees",
        json={"name": "L2", "amount": 20000},
        headers=headers,
    )
    assert over.status_code == 409


def test_partial_then_full_deposit_payment(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    deposit_id = client.post(
        f"/api/v1/deposits/openings/{opening['id']}",
        json={"total_amount": 42000},
        headers=headers,
    ).json()["id"]
    payee_id = client.post(
        f"/api/v1/deposits/{deposit_id}/payees",
        json={"name": "Landlord", "amount": 21000},
        headers=headers,
    ).json()["id"]

    partial = client.post(
        f"/api/v1/deposits/payees/{payee_id}/payments",
        json={"amount": 10000, "payment_date": "2026-08-12", "reference": "NEFT-1"},
        headers=headers,
    )
    assert partial.status_code == 201, partial.text

    detail = client.get(f"/api/v1/deposits/{deposit_id}", headers=headers).json()
    assert detail["status"] == "PARTIALLY_PAID"
    assert detail["payees"][0]["paid_amount"] == 10000
    assert detail["payees"][0]["status"] == "APPROVED"

    rest = client.post(
        f"/api/v1/deposits/payees/{payee_id}/payments",
        json={"amount": 11000, "payment_date": "2026-08-13", "reference": "NEFT-2"},
        headers=headers,
    )
    assert rest.status_code == 201

    detail = client.get(f"/api/v1/deposits/{deposit_id}", headers=headers).json()
    assert detail["status"] == "PARTIALLY_PAID"
    assert detail["paid_amount"] == 21000
    assert detail["payees"][0]["status"] == "PAID"

    payee2_id = client.post(
        f"/api/v1/deposits/{deposit_id}/payees",
        json={"name": "Landlord 2", "amount": 21000},
        headers=headers,
    ).json()["id"]
    client.post(
        f"/api/v1/deposits/payees/{payee2_id}/payments",
        json={"amount": 21000, "payment_date": "2026-08-14", "reference": "NEFT-3"},
        headers=headers,
    )

    detail = client.get(f"/api/v1/deposits/{deposit_id}", headers=headers).json()
    assert detail["status"] == "PAID"
    assert detail["paid_amount"] == 42000


def test_deposit_overpayment_prevented(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    deposit_id = client.post(
        f"/api/v1/deposits/openings/{opening['id']}",
        json={"total_amount": 42000},
        headers=headers,
    ).json()["id"]
    payee_id = client.post(
        f"/api/v1/deposits/{deposit_id}/payees",
        json={"name": "Landlord", "amount": 21000},
        headers=headers,
    ).json()["id"]

    client.post(
        f"/api/v1/deposits/payees/{payee_id}/payments",
        json={"amount": 21000},
        headers=headers,
    )
    overpay = client.post(
        f"/api/v1/deposits/payees/{payee_id}/payments",
        json={"amount": 100},
        headers=headers,
    )
    assert overpay.status_code == 409


def test_loa_lifecycle(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    created = client.post(
        f"/api/v1/loa/openings/{opening['id']}",
        json={
            "employee": "Sanjay Gupta",
            "employee_code": "5288",
            "agreement_tenure": "01-Sep-2026 to 31-Jul-2027",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    loa = created.json()
    assert loa["status"] == "REQUESTED"

    for status_value in ("APPROVED", "ISSUED", "EXECUTED"):
        updated = client.patch(
            f"/api/v1/loa/{loa['id']}",
            json={"status": status_value},
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == status_value

    executed = client.get(f"/api/v1/loa/{loa['id']}", headers=headers).json()
    assert executed["issued_date"] is not None


def test_loa_invalid_transition_rejected(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    loa = client.post(
        f"/api/v1/loa/openings/{opening['id']}",
        json={"employee": "E", "employee_code": "1"},
        headers=headers,
    ).json()

    invalid = client.patch(
        f"/api/v1/loa/{loa['id']}",
        json={"status": "EXECUTED"},
        headers=headers,
    )
    assert invalid.status_code == 409


def test_loa_rejected_flow(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    loa = client.post(
        f"/api/v1/loa/openings/{opening['id']}",
        json={"employee": "E", "employee_code": "1"},
        headers=headers,
    ).json()

    rejected = client.patch(
        f"/api/v1/loa/{loa['id']}",
        json={"status": "REJECTED", "remarks": "wrong name"},
        headers=headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"


def test_sd_role_can_manage_deposits(client) -> None:
    from conftest import ensure_user, login

    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    ensure_user("SD", "sd_user")
    sd_token = login(client, "sd_user@example.com")
    sd_headers = {"Authorization": f"Bearer {sd_token}"}

    created = client.post(
        f"/api/v1/deposits/openings/{opening['id']}",
        json={"total_amount": 42000},
        headers=sd_headers,
    )
    assert created.status_code == 201