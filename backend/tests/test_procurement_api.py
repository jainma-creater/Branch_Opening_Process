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


def _vendors(client, headers: dict, count: int = 3) -> list[dict]:
    vendors = []
    for index in range(count):
        created = client.post(
            "/api/v1/procurement/vendors",
            json={"name": f"Vendor {index + 1}", "contact_person": f"P{index + 1}"},
            headers=headers,
        )
        assert created.status_code == 201, created.text
        vendors.append(created.json())
    return vendors


def _request(client, opening_id: int, headers: dict) -> dict:
    created = client.post(
        f"/api/v1/procurement/quotation-requests/openings/{opening_id}",
        json={
            "scope_description": "Furniture and electrical fit-out",
            "items": [
                {"category": "FIXED_ASSETS", "description": "Workstations", "quantity": 6},
                {"category": "ELECTRICAL", "description": "Wiring", "quantity": 1},
                {"category": "RENOVATION", "description": "Painting", "quantity": 1},
            ],
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()


def _quotation(client, request_id: int, vendor_id: int, headers: dict, rate: float) -> dict:
    created = client.post(
        f"/api/v1/procurement/quotation-requests/{request_id}/quotations",
        json={
            "vendor_id": vendor_id,
            "items": [
                {"category": "FIXED_ASSETS", "description": "Workstations", "quantity": 6, "rate": rate, "tax": 10},
                {"category": "ELECTRICAL", "description": "Wiring", "quantity": 1, "rate": 1000, "tax": 0},
            ],
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()


def test_three_vendor_quotation_flow(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendors = _vendors(client, headers)
    request = _request(client, opening["id"], headers)
    request_id = request["id"]

    quotes = [
        _quotation(client, request_id, vendors[0]["id"], headers, 9000),
        _quotation(client, request_id, vendors[1]["id"], headers, 8000),
        _quotation(client, request_id, vendors[2]["id"], headers, 9500),
    ]
    assert len(quotes) == 3


def test_quotation_amount_calculation(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendor = _vendors(client, headers, 1)[0]
    request = _request(client, opening["id"], headers)

    quote = _quotation(client, request["id"], vendor["id"], headers, 10000)
    # workstation: 6 x 10000 + 10% tax = 66000; wiring: 1000 -> total 67000
    assert float(quote["total_amount"]) == 67000.0
    items = {i["description"]: i for i in quote["items"]}
    assert float(items["Workstations"]["amount"]) == 60000.0
    assert float(items["Workstations"]["final_amount"]) == 66000.0


def test_comparison_ranking_l1_l2_l3(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendors = _vendors(client, headers)
    request = _request(client, opening["id"], headers)

    _quotation(client, request["id"], vendors[0]["id"], headers, 9000)
    _quotation(client, request["id"], vendors[1]["id"], headers, 8000)
    _quotation(client, request["id"], vendors[2]["id"], headers, 9500)

    comparison = client.get(
        f"/api/v1/procurement/quotation-requests/{request['id']}/comparison",
        headers=headers,
    ).json()

    assert len(comparison["rows"]) == 3
    # vendor1: 6x8000 +10% tax = 52800 + 1000 wiring = 53800 (L1)
    # vendor0: 6x9000 +10% tax = 59400 + 1000 wiring = 60400 (L2)
    # vendor2: 6x9500 +10% tax = 62700 + 1000 wiring = 63700 (L3)
    assert comparison["rows"][0]["total_amount"] == 53800.0
    assert comparison["rows"][1]["total_amount"] == 60400.0
    assert comparison["rows"][2]["total_amount"] == 63700.0
    assert [r["rank"] for r in comparison["rows"]] == [1, 2, 3]
    assert comparison["lowest_amount"] == 53800.0
    assert comparison["highest_amount"] == 63700.0
    assert comparison["difference"] == 9900.0
    assert comparison["average_amount"] == 59300.0


def test_manual_vendor_selection_not_l1_forced(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendors = _vendors(client, headers)
    request = _request(client, opening["id"], headers)

    _quotation(client, request["id"], vendors[0]["id"], headers, 8000)  # L1
    _quotation(client, request["id"], vendors[1]["id"], headers, 9000)
    _quotation(client, request["id"], vendors[2]["id"], headers, 7000)  # cheaper

    comparison = client.get(
        f"/api/v1/procurement/quotation-requests/{request['id']}/comparison",
        headers=headers,
    ).json()
    assert comparison["rows"][0]["rank"] == 1

    # business decision: pick vendor 2 (NOT the lowest)
    selected = client.post(
        f"/api/v1/procurement/quotation-requests/{request['id']}/select-vendor",
        json={"vendor_id": vendors[1]["id"], "comments": "better service record"},
        headers=headers,
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["selected_vendor_id"] == vendors[1]["id"]
    assert selected.json()["status"] == "APPROVED"

    accepted = [q for q in selected.json()["quotations"] if q["vendor"]["id"] == vendors[1]["id"]][0]
    assert accepted["status"] == "ACCEPTED"


def test_cannot_select_unquoted_vendor(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendors = _vendors(client, headers)
    request = _request(client, opening["id"], headers)
    _quotation(client, request["id"], vendors[0]["id"], headers, 8000)

    rejected = client.post(
        f"/api/v1/procurement/quotation-requests/{request['id']}/select-vendor",
        json={"vendor_id": vendors[1]["id"]},
        headers=headers,
    )
    assert rejected.status_code == 409


def test_duplicate_vendor_quotation_rejected(client) -> None:
    structure = org_structure(client)
    headers = {"Authorization": f"Bearer {structure['token']}"}
    opening = _open(client, structure, headers)
    vendor = _vendors(client, headers, 1)[0]
    request_id = _request(client, opening["id"], headers)["id"]

    _quotation(client, request_id, vendor["id"], headers, 8000)
    duplicate = client.post(
        f"/api/v1/procurement/quotation-requests/{request_id}/quotations",
        json={
            "vendor_id": vendor["id"],
            "items": [{"category": "OTHER", "description": "x", "quantity": 1, "rate": 100}],
        },
        headers=headers,
    )
    assert duplicate.status_code == 409