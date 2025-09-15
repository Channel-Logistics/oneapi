from datetime import datetime, timezone, timedelta


def test_orders_crud(client):
    # Create with explicit datetime fields and non-null bbox list
    now = datetime.now(timezone.utc)
    payload = {
        "bbox": [-75.58, 10.37, -75.49, 10.43],
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(hours=1)).isoformat(),
        "status": "pending",
    }
    r = client.post("/orders", json=payload)
    assert r.status_code == 201, r.text
    created = r.json()
    order_id = created["id"]
    assert created["status"] == "pending"

    # Get by id
    r = client.get(f"/orders/{order_id}")
    assert r.status_code == 200, r.text
    assert r.json()["id"] == order_id

    # List (filter by status)
    r = client.get("/orders", params={"status": "pending", "limit": 50, "offset": 0})
    assert r.status_code == 200, r.text
    assert any(o["id"] == order_id for o in r.json())

    # Patch -> processing
    r = client.patch(f"/orders/{order_id}", json={"status": "processing"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "processing"

    # Delete
    r = client.delete(f"/orders/{order_id}")
    assert r.status_code == 204, r.text

    # Ensure gone
    r = client.get(f"/orders/{order_id}")
    assert r.status_code == 404, r.text
