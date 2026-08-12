from datetime import date

from conftest import admin_token, ensure_user, login, org_structure


def _create(client, structure: dict, headers: dict, branch_id: int | None = None) -> dict:
    response = client.post(
        "/api/v1/openings",
        json={
            "branch_id": branch_id or structure["branch_id"],
            "project_type": "NEW_BRANCH",
            "business_reason": "Business expansion",
            "requested_date": date(2026, 8, 11).isoformat(),
            "tentative_operations_date": date(2026, 12, 1).isoformat(),
        },
        headers=headers,
    )
    return response


def test_create_opening_generates_case_number(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    response = _create(client, structure, headers)
    assert response.status_code == 201, response.text
    opening = response.json()
    assert opening["opening_number"] == "BO-2026-0001"
    assert opening["case_status"] == "ACTIVE"
    assert opening["current_stage"] == "REQUIREMENT"
    assert opening["branch"]["name"] == "Khandwa"
    assert opening["area"]["name"] == "Indore"
    assert opening["region"]["name"] == "Madhya Pradesh"
    assert len(opening["workflow_instances"]) == 15
    assert opening["pending_tasks"] == 0


def test_case_number_sequence_increments(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    first = _create(client, structure, headers).json()
    second = _create(client, structure, headers).json()
    assert first["opening_number"] == "BO-2026-0001"
    assert second["opening_number"] == "BO-2026-0002"


def test_create_opening_requires_valid_branch(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    response = _create(client, structure, headers, branch_id=9999)
    assert response.status_code == 422


def test_duplicate_prevention_by_unique_number(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    first = _create(client, structure, headers).json()
    listed = client.get(
        f"/api/v1/openings?search={first['opening_number']}", headers=headers
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["opening_number"] == first["opening_number"]


def test_list_and_filters(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    _create(client, structure, headers)
    _create(client, structure, headers)

    by_branch = client.get(
        f"/api/v1/openings?branch_id={structure['branch_id']}", headers=headers
    )
    assert len(by_branch.json()) == 2

    by_region = client.get(
        f"/api/v1/openings?region_id={structure['region_id']}", headers=headers
    )
    assert len(by_region.json()) == 2

    by_status = client.get("/api/v1/openings?case_status=ACTIVE", headers=headers)
    assert len(by_status.json()) == 2

    by_stage = client.get("/api/v1/openings?current_stage=REQUIREMENT", headers=headers)
    assert len(by_stage.json()) == 2

    not_found = client.get("/api/v1/openings?case_status=COMPLETED", headers=headers)
    assert len(not_found.json()) == 0


def test_opening_detail_and_pending_stages(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create(client, structure, headers).json()

    detail = client.get(f"/api/v1/openings/{opening['id']}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["opening_number"] == opening["opening_number"]
    assert len(body["pending_stages"]) == 15
    assert len(body["completed_stages"]) == 0
    assert body["pending_stages"][0]["code"] == "REQUIREMENT"


def test_update_and_status_change(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create(client, structure, headers).json()

    updated = client.patch(
        f"/api/v1/openings/{opening['id']}",
        json={"business_reason": "Updated reason"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["business_reason"] == "Updated reason"

    on_hold = client.patch(
        f"/api/v1/openings/{opening['id']}/status",
        json={"case_status": "ON_HOLD"},
        headers=headers,
    )
    assert on_hold.status_code == 200
    assert on_hold.json()["case_status"] == "ON_HOLD"

    completed = client.patch(
        f"/api/v1/openings/{opening['id']}/status",
        json={"case_status": "COMPLETED"},
        headers=headers,
    )
    assert completed.json()["completed_at"] is not None


def test_assign_opening(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _create(client, structure, headers).json()

    user = ensure_user("ADMIN", "assignee")
    response = client.post(
        f"/api/v1/openings/{opening['id']}/assign",
        json={"assigned_to": user.id},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["assigned_to"] == user.id


def test_business_team_can_create_but_not_approve(client) -> None:
    structure = org_structure(client)
    ensure_user("BUSINESS_TEAM", "bt_open")
    bt_token = login(client, "bt_open@example.com")
    bt_headers = {"Authorization": f"Bearer {bt_token}"}

    created = _create(client, structure, bt_headers)
    assert created.status_code == 201

    opening = created.json()
    forbidden = client.patch(
        f"/api/v1/openings/{opening['id']}",
        json={"business_reason": "nope"},
        headers=bt_headers,
    )
    assert forbidden.status_code == 403


def test_regional_admin_scoped_to_own_region(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    _create(client, structure, headers)

    ensure_user("REGIONAL_ADMIN", "ra_other", name="Other Regional")
    ra_token = login(client, "ra_other@example.com")
    ra_headers = {"Authorization": f"Bearer {ra_token}"}

    visible = client.get("/api/v1/openings", headers=ra_headers)
    assert len(visible.json()) == 1


def test_unauthenticated_denied(client) -> None:
    response = client.get("/api/v1/openings")
    assert response.status_code in (401, 403)