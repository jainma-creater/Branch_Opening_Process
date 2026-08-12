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


def _add_property(client, opening_id: int, headers: dict, **overrides) -> dict:
    payload = {
        "address": "12 MG Road, Khandwa",
        "area_sqft": 700,
        "rent": 14000,
        "deposit": 42000,
        "annual_increment": 5,
        "entrance": "YES",
        "restroom": "YES",
        "possession_status": "IMMEDIATE",
        "remarks": "main road property",
    }
    payload.update(overrides)
    response = client.post(
        f"/api/v1/properties/openings/{opening_id}", json=payload, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_multiple_properties_with_sequence(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    first = _add_property(client, opening["id"], headers, address="Option A Street")
    second = _add_property(client, opening["id"], headers, address="Option B Street")
    third = _add_property(client, opening["id"], headers, address="Option C Street")

    assert first["option_sequence"] == 1
    assert second["option_sequence"] == 2
    assert third["option_sequence"] == 3

    listed = client.get(
        f"/api/v1/properties/openings/{opening['id']}", headers=headers
    ).json()
    assert [p["option_sequence"] for p in listed] == [1, 2, 3]


def test_rent_limit_check_against_branch_limit(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    within = _add_property(client, opening["id"], headers, rent=12000)
    above = _add_property(client, opening["id"], headers, rent=15000, address="Costly Road")

    assert within["rent_limit_check"] == "WITHIN_LIMIT"
    assert above["rent_limit_check"] == "ABOVE_LIMIT"
    assert float(above["applicable_rent_limit"]) == 12000.0


def test_property_approval_creates_approval_record(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    option = _add_property(client, opening["id"], headers)

    approval_requested = client.post(
        f"/api/v1/properties/{option['id']}/approval-request", headers=headers
    )
    assert approval_requested.status_code == 200
    assert approval_requested.json()["status"] == "UNDER_APPROVAL"

    approved = client.post(f"/api/v1/properties/{option['id']}/approve", headers=headers)
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"


def test_property_cancel_preserves_history_then_replacement(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    property_a = _add_property(client, opening["id"], headers, address="Property A")
    client.post(f"/api/v1/properties/{property_a['id']}/approve", headers=headers)

    cancelled = client.post(
        f"/api/v1/properties/{property_a['id']}/cancel",
        json={"remarks": "owner backed out"},
        headers=headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"

    property_b = _add_property(
        client, opening["id"], headers, address="Property B Replacement"
    )
    assert property_b["status"] == "REPLACEMENT"
    assert property_b["option_sequence"] == 2

    under_approval = client.post(
        f"/api/v1/properties/{property_b['id']}/approval-request", headers=headers
    )
    assert under_approval.json()["status"] == "UNDER_APPROVAL"

    listed = client.get(
        f"/api/v1/properties/openings/{opening['id']}", headers=headers
    ).json()
    assert {p["address"] for p in listed} == {"Property A", "Property B Replacement"}
    assert listed[0]["status"] == "CANCELLED"
    assert listed[1]["status"] == "UNDER_APPROVAL"


def test_cancelled_property_cannot_be_approved(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    option = _add_property(client, opening["id"], headers)
    client.post(f"/api/v1/properties/{option['id']}/cancel", headers=headers)

    rejected = client.post(
        f"/api/v1/properties/{option['id']}/approval-request", headers=headers
    )
    assert rejected.status_code == 409


def test_property_rejected_and_not_selected_statuses(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    option = _add_property(client, opening["id"], headers)

    rejected = client.patch(
        f"/api/v1/properties/{option['id']}/status",
        json={"status": "REJECTED", "remarks": "too small"},
        headers=headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"

    option2 = _add_property(client, opening["id"], headers, address="Another")
    marked = client.patch(
        f"/api/v1/properties/{option2['id']}/status",
        json={"status": "NOT_SELECTED"},
        headers=headers,
    )
    assert marked.json()["status"] == "NOT_SELECTED"


def test_business_team_cannot_manage_properties(client) -> None:
    from conftest import ensure_user, login

    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    ensure_user("BUSINESS_TEAM", "bt_prop")
    bt_token = login(client, "bt_prop@example.com")
    forbidden = client.post(
        f"/api/v1/properties/openings/{opening['id']}",
        json={"address": "X"},
        headers={"Authorization": f"Bearer {bt_token}"},
    )
    assert forbidden.status_code == 403