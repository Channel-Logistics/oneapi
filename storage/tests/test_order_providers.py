from datetime import datetime, timedelta, timezone


def test_order_providers_crud(client):
    # Create a provider (idempotent on slug)
    r = client.post(
        "/providers",
        json={
            "slug": "prov-tests",
            "name": "Prov Tests",
            "sensor_types": [],
            "active": True,
        },
    )
    if r.status_code == 409:
        r = client.get("/providers?limit=200&offset=0")
        assert r.status_code == 200, r.text
        provs = [p for p in r.json() if p["slug"] == "prov-tests"]
        if provs:
            provider_id = provs[0]["id"]
        else:
            r = client.post(
                "/providers",
                json={
                    "slug": "prov-tests-2",
                    "name": "Prov Tests 2",
                    "sensor_types": [],
                    "active": True,
                },
            )
            assert r.status_code == 201, r.text
            provider_id = r.json()["id"]
    else:
        assert r.status_code == 201, r.text
        provider_id = r.json()["id"]

    # Create an order (strict-friendly payload)
    now = datetime.now(timezone.utc)
    order_payload = {
        "bbox": [-75.0, 10.0, -74.9, 10.1],
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(hours=1)).isoformat(),
        "status": "pending",
    }
    r = client.post("/orders", json=order_payload)
    assert r.status_code == 201, r.text
    order_id = r.json()["id"]

    try:
        # Create order_provider link
        payload = {
            "order_id": order_id,
            "provider_id": provider_id,
            "status": "pending",
            "meta": {},
        }
        r = client.post("/order-providers", json=payload)
        assert r.status_code == 201, r.text
        op_obj = r.json()
        op_id = op_obj["id"]

        # Get by id
        r = client.get(f"/order-providers/{op_id}")
        assert r.status_code == 200, r.text
        assert r.json()["id"] == op_id

        # List with filters
        r = client.get("/order-providers", params={"order_id": order_id})
        assert r.status_code == 200, r.text
        assert any(x["id"] == op_id for x in r.json())

        # Patch status
        r = client.patch(f"/order-providers/{op_id}", json={"status": "done"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "done"

        # Delete link
        r = client.delete(f"/order-providers/{op_id}")
        assert r.status_code == 204, r.text

        # Ensure gone
        r = client.get(f"/order-providers/{op_id}")
        assert r.status_code == 404, r.text
    finally:
        # Cleanup
        client.delete(f"/orders/{order_id}")
        client.delete(f"/providers/{provider_id}")
