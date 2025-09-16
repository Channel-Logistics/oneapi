from datetime import datetime, timezone, timedelta


def test_events_crud_under_order(client):
    # Create an order with explicit fields (works for strict/loose schemas)
    now = datetime.now(timezone.utc)
    order_payload = {
        "bbox": [-75.0, 10.0, -74.9, 10.1],
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(hours=1)).isoformat(),
        "status": "pending",
    }
    r = client.post("/orders", json=order_payload)
    assert r.status_code == 201, r.text
    order = r.json()
    order_id = order["id"]

    try:
        # Initially empty list
        r = client.get(f"/orders/{order_id}/events")
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

        # Create one event
        evt_payload = {"type": "created", "data": {"source": "tests"}}
        r = client.post(f"/orders/{order_id}/events", json=evt_payload)
        assert r.status_code == 201, r.text
        evt = r.json()
        assert evt["order_id"] == order_id
        assert evt["type"] == "created"

        # List should include it
        r = client.get(f"/orders/{order_id}/events")
        assert r.status_code == 200, r.text
        items = r.json()
        assert any(e["id"] == evt["id"] for e in items)
    finally:
        # Cleanup: delete order (cascade should remove events)
        client.delete(f"/orders/{order_id}")
