def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("ok") is True
