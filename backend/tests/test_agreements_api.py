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


def test_agreement_with_multiple_licensors(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    created = client.post(
        f"/api/v1/agreements/openings/{opening['id']}",
        json={
            "agreement_date": "2026-08-20",
            "start_date": "2026-09-01",
            "end_date": "2027-07-31",
            "tenure": "11 months",
            "monthly_rent": 14000,
            "annual_increment": 5,
            "security_deposit": 42000,
            "lock_in": "11 months",
            "fitout_period": "45 days",
            "parties": [
                {
                    "party_type": "LICENSOR",
                    "name": "Licensor One",
                    "email": "l1@example.com",
                    "phone": "9811111111",
                },
                {
                    "party_type": "LICENSOR",
                    "name": "Licensor Two",
                    "email": "l2@example.com",
                    "phone": "9822222222",
                },
                {
                    "party_type": "LICENSEE",
                    "name": "Svatantra MHFC Ltd",
                    "details": "Branch Khandwa",
                },
            ],
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    agreement = created.json()
    assert agreement["monthly_rent"] == 14000
    assert agreement["start_date"] == "2026-09-01"
    assert agreement["end_date"] == "2027-07-31"
    assert agreement["status"] == "DRAFT"
    licensors = [p for p in agreement["parties"] if p["party_type"] == "LICENSOR"]
    assert len(licensors) == 2


def test_agreement_execution_lifecycle(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    agreement = client.post(
        f"/api/v1/agreements/openings/{opening['id']}",
        json={"monthly_rent": 14000, "security_deposit": 42000},
        headers=headers,
    ).json()

    for status_value, expected_prev in (("UNDER_EXECUTION", "DRAFT"), ("EXECUTED", "UNDER_EXECUTION")):
        updated = client.patch(
            f"/api/v1/agreements/{agreement['id']}/status",
            json={"status": status_value, "remarks": f"from {expected_prev}"},
            headers=headers,
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["status"] == status_value

    listed = client.get(
        f"/api/v1/agreements/openings/{opening['id']}", headers=headers
    ).json()
    assert len(listed) == 1
    assert listed[0]["status"] == "EXECUTED"


def test_agreement_update_preserves_fields(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    agreement = client.post(
        f"/api/v1/agreements/openings/{opening['id']}",
        json={"monthly_rent": 14000},
        headers=headers,
    ).json()

    updated = client.patch(
        f"/api/v1/agreements/{agreement['id']}",
        json={"annual_increment": 7, "lock_in": "12 months"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["annual_increment"] == 7
    assert updated.json()["monthly_rent"] == 14000

    cancelled = client.patch(
        f"/api/v1/agreements/{agreement['id']}/status",
        json={"status": "CANCELLED", "remarks": "terms changed"},
        headers=headers,
    )
    assert cancelled.json()["status"] == "CANCELLED"


def test_agreement_requires_opening(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    response = client.post(
        "/api/v1/agreements/openings/9999",
        json={"monthly_rent": 10000},
        headers=headers,
    )
    assert response.status_code == 404


def test_business_team_cannot_manage_agreements(client) -> None:
    from conftest import ensure_user, login

    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)

    ensure_user("BUSINESS_TEAM", "bt_agr")
    bt_token = login(client, "bt_agr@example.com")
    response = client.post(
        f"/api/v1/agreements/openings/{opening['id']}",
        json={"monthly_rent": 10000},
        headers={"Authorization": f"Bearer {bt_token}"},
    )
    assert response.status_code == 403