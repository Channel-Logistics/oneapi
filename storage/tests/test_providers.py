import uuid


def test_providers_crud(client):
    # Create
    slug = f"prov-{uuid.uuid4().hex[:8]}"
    payload = {
        "slug": slug,
        "name": "UP42",
        "sensor_types": ["EO"],
        "active": True,
    }
    r = client.post("/providers", json=payload)
    assert r.status_code == 201, r.text
    provider = r.json()
    provider_id = provider["id"]

    # Get
    r = client.get(f"/providers/{provider_id}")
    assert r.status_code == 200, r.text

    # List
    r = client.get("/providers?limit=5&offset=0")
    assert r.status_code == 200, r.text
    assert any(p["id"] == provider_id for p in r.json())

    # Patch
    r = client.patch(f"/providers/{provider_id}", json={"name": "UP42 Updated"})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "UP42 Updated"

    # Delete
    r = client.delete(f"/providers/{provider_id}")
    assert r.status_code == 204, r.text

    # 404 afterwards
    r = client.get(f"/providers/{provider_id}")
    assert r.status_code == 404, r.text
