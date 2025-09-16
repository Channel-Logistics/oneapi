import pytest

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_events_404_when_order_missing_http(async_client, mock_session):
    mock_session.get.return_value = None
    r = await async_client.get("/orders/abc/events")
    assert r.status_code == 404
    assert r.json()["detail"] == "order not found"
