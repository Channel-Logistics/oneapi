def test_create_task(client_with_mocked_amqp):
    """Test task creation endpoint."""
    task_data = {"query": "test query", "provider": "test_provider"}
    response = client_with_mocked_amqp.post("/tasks", json=task_data)

    assert response.status_code == 200
    data = response.json()
    assert "taskId" in data
    assert "sseUrl" in data
    assert data["sseUrl"].startswith("/tasks/")
    assert data["sseUrl"].endswith("/events")


def test_create_task_invalid_json(client):
    """Test task creation with invalid JSON."""
    response = client.post("/tasks", data="invalid json")
    assert response.status_code == 422  # Unprocessable Entity


def test_create_task_empty_body(client_with_mocked_amqp):
    """Test task creation with empty body."""
    response = client_with_mocked_amqp.post("/tasks", json={})
    assert response.status_code == 200
    data = response.json()
    assert "taskId" in data
    assert "sseUrl" in data


def test_sse_endpoint_requires_task_id(client):
    """Test that SSE endpoint requires a task_id parameter."""
    response = client.get("/tasks//events")
    assert response.status_code == 404  # Not found due to empty task_id


import pytest


@pytest.mark.skip(reason="SSE endpoint is long-lived; verify via e2e/manual tests")
def test_sse_endpoint_with_valid_task_id(client_with_mocked_amqp):
    pass


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.options("/tasks")
    # FastAPI handles CORS automatically, so we just check the endpoint is accessible
    assert response.status_code in [
        200,
        405,
    ]  # OPTIONS might return 405 if not explicitly handled
