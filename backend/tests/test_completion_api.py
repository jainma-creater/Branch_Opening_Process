from conftest import _test_session, org_structure


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


def test_fitout_completion_advances_to_readiness(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "INFRASTRUCTURE")

    created = client.post(
        f"/api/v1/completion/openings/{opening['id']}/fitouts",
        json={"scope": "Electrical and painting"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    fitout_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/completion/fitouts/{fitout_id}",
        json={"status": "COMPLETED"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "COMPLETED"
    assert _opening_stage(opening["id"]) == "OPERATIONAL_READINESS"


def test_readiness_all_done_advances_to_opening(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "OPERATIONAL_READINESS")

    items = []
    for name in ("Power connection", "Internet", "Staffing"):
        created = client.post(
            f"/api/v1/completion/openings/{opening['id']}/readiness",
            json={"item_name": name},
            headers=headers,
        )
        assert created.status_code == 201, created.text
        items.append(created.json()["id"])

    for item_id in items:
        done = client.patch(
            f"/api/v1/completion/readiness/{item_id}",
            json={"status": "DONE"},
            headers=headers,
        )
        assert done.status_code == 200, done.text

    assert _opening_stage(opening["id"]) == "OPENING"


def test_opening_record_completes_case(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    _set_stage(opening["id"], "OPENING")

    record = client.post(
        f"/api/v1/completion/openings/{opening['id']}/opening-record",
        json={"opening_date": "2026-09-01", "inaugurated_by": "MD"},
        headers=headers,
    )
    assert record.status_code == 201, record.text
    assert _opening_stage(opening["id"]) == "COMPLETED"
