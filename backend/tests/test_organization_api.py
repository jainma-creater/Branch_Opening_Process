from conftest import admin_token, org_structure


def _headers(client) -> dict:
    return {"Authorization": f"Bearer {admin_token(client)}"}


def test_region_crud(client) -> None:
    headers = _headers(client)

    created = client.post(
        "/api/v1/organization/regions",
        json={"name": "Madhya Pradesh", "rent_limit": 85000},
        headers=headers,
    )
    assert created.status_code == 201
    region_json = created.json()
    assert region_json["name"] == "Madhya Pradesh"
    assert float(region_json["rent_limit"]) == 85000.0

    fetched = client.get(f"/api/v1/organization/regions/{region_json['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Madhya Pradesh"

    listed = client.get("/api/v1/organization/regions", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/v1/organization/regions/{region_json['id']}",
        json={"rent_limit": 90000},
        headers=headers,
    )
    assert updated.status_code == 200
    assert float(updated.json()["rent_limit"]) == 90000.0


def test_duplicate_region_rejected(client) -> None:
    headers = _headers(client)
    payload = {"name": "Telangana", "rent_limit": 85000}

    first = client.post("/api/v1/organization/regions", json=payload, headers=headers)
    assert first.status_code == 201

    duplicate = client.post("/api/v1/organization/regions", json=payload, headers=headers)
    assert duplicate.status_code == 409


def test_area_requires_valid_region(client) -> None:
    headers = _headers(client)

    orphan = client.post(
        "/api/v1/organization/areas",
        json={"region_id": 9999, "name": "Orphan"},
        headers=headers,
    )
    assert orphan.status_code == 422


def test_duplicate_area_in_region_rejected(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    payload = {"region_id": structure["region_id"], "name": "Indore"}

    duplicate = client.post("/api/v1/organization/areas", json=payload, headers=headers)
    assert duplicate.status_code == 409


def test_branch_requires_valid_area_and_unique_code(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    invalid_area = client.post(
        "/api/v1/organization/branches",
        json={"area_id": 9999, "name": "X", "branch_code": "SMHFC_X"},
        headers=headers,
    )
    assert invalid_area.status_code == 422

    duplicate_code = client.post(
        "/api/v1/organization/branches",
        json={
            "area_id": structure["area_id"],
            "name": "Khandwa Clone",
            "branch_code": "SMHFC_B00145",
        },
        headers=headers,
    )
    assert duplicate_code.status_code == 409


def test_hierarchy_relationship_lists(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    areas = client.get(
        f"/api/v1/organization/areas?region_id={structure['region_id']}", headers=headers
    )
    assert areas.status_code == 200
    assert areas.json()[0]["id"] == structure["area_id"]

    branches = client.get(
        f"/api/v1/organization/branches?area_id={structure['area_id']}", headers=headers
    )
    assert branches.status_code == 200
    assert branches.json()[0]["id"] == structure["branch_id"]

    region = client.get(f"/api/v1/organization/regions/{structure['region_id']}", headers=headers)
    assert region.json()["area_count"] == 1
    assert region.json()["branch_count"] == 1


def test_business_team_cannot_create(client) -> None:
    from conftest import ensure_user, login

    ensure_user("BUSINESS_TEAM", "bt_user")
    token = login(client, "bt_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    forbidden = client.post(
        "/api/v1/organization/regions",
        json={"name": "Rogue", "rent_limit": 100},
        headers=headers,
    )
    assert forbidden.status_code == 403


def test_unauthenticated_rejected(client) -> None:
    response = client.get("/api/v1/organization/regions")
    assert response.status_code in (401, 403)


def test_delete_region_with_children_conflict(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}

    response = client.delete(
        f"/api/v1/organization/regions/{structure['region_id']}", headers=headers
    )
    assert response.status_code == 409


def test_delete_empty_region_succeeds(client) -> None:
    headers = _headers(client)
    created = client.post(
        "/api/v1/organization/regions", json={"name": "Empty"}, headers=headers
    ).json()

    response = client.delete(f"/api/v1/organization/regions/{created['id']}", headers=headers)
    assert response.status_code == 204