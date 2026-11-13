"""Tests for the /tasks endpoints, including per-user ownership rules."""

_PASSWORD = "s3cr3t!"


def _headers(client, email):
    """Register a user and return an Authorization header for them."""
    resp = client.post("/auth/register", json={"email": email, "password": _PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create(client, headers, **overrides):
    body = {"name": "Summarise a document", "difficulty": "easy"}
    body.update(overrides)
    return client.post("/tasks", json=body, headers=headers)


# -- Create ---------------------------------------------------------------


def test_create_task_returns_201_and_fields(client):
    h = _headers(client, "a@example.com")
    resp = _create(client, h, description="Short summary", expected_output="A summary")
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Summarise a document"
    assert data["difficulty"] == "easy"
    assert data["expected_output"] == "A summary"
    assert "id" in data


def test_create_task_default_difficulty_is_medium(client):
    h = _headers(client, "a@example.com")
    resp = client.post("/tasks", json={"name": "No difficulty given"}, headers=h)
    assert resp.status_code == 201
    assert resp.json()["difficulty"] == "medium"


def test_create_task_without_token_returns_401(client):
    assert client.post("/tasks", json={"name": "x"}).status_code == 401


def test_create_task_invalid_difficulty_returns_422(client):
    h = _headers(client, "a@example.com")
    assert _create(client, h, difficulty="impossible").status_code == 422


def test_create_task_empty_name_returns_422(client):
    h = _headers(client, "a@example.com")
    assert _create(client, h, name="").status_code == 422


# -- List and read ---------------------------------------------------------


def test_list_tasks_empty(client):
    h = _headers(client, "a@example.com")
    assert client.get("/tasks", headers=h).json() == []


def test_list_tasks_returns_only_own_tasks(client):
    a = _headers(client, "a@example.com")
    b = _headers(client, "b@example.com")
    _create(client, a, name="A1")
    _create(client, a, name="A2")
    _create(client, b, name="B1")
    names_a = [t["name"] for t in client.get("/tasks", headers=a).json()]
    names_b = [t["name"] for t in client.get("/tasks", headers=b).json()]
    assert names_a == ["A1", "A2"]
    assert names_b == ["B1"]


def test_get_own_task_returns_200(client):
    h = _headers(client, "a@example.com")
    task_id = _create(client, h).json()["id"]
    assert client.get(f"/tasks/{task_id}", headers=h).status_code == 200


def test_get_missing_task_returns_404(client):
    h = _headers(client, "a@example.com")
    assert client.get("/tasks/9999", headers=h).status_code == 404


# -- Update and delete -----------------------------------------------------


def test_update_own_task(client):
    h = _headers(client, "a@example.com")
    task_id = _create(client, h).json()["id"]
    resp = client.put(
        f"/tasks/{task_id}",
        json={"name": "Renamed", "difficulty": "hard"},
        headers=h,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    assert resp.json()["difficulty"] == "hard"


def test_delete_own_task_returns_204_then_404(client):
    h = _headers(client, "a@example.com")
    task_id = _create(client, h).json()["id"]
    assert client.delete(f"/tasks/{task_id}", headers=h).status_code == 204
    assert client.get(f"/tasks/{task_id}", headers=h).status_code == 404


# -- Ownership: user B must not touch user A's task ------------------------


def test_other_user_cannot_read_task(client):
    a = _headers(client, "a@example.com")
    b = _headers(client, "b@example.com")
    task_id = _create(client, a).json()["id"]
    assert client.get(f"/tasks/{task_id}", headers=b).status_code == 404


def test_other_user_cannot_update_task(client):
    a = _headers(client, "a@example.com")
    b = _headers(client, "b@example.com")
    task_id = _create(client, a).json()["id"]
    resp = client.put(f"/tasks/{task_id}", json={"name": "Hacked"}, headers=b)
    assert resp.status_code == 404
    # The owner's task must be unchanged.
    assert client.get(f"/tasks/{task_id}", headers=a).json()["name"] == "Summarise a document"


def test_other_user_cannot_delete_task(client):
    a = _headers(client, "a@example.com")
    b = _headers(client, "b@example.com")
    task_id = _create(client, a).json()["id"]
    assert client.delete(f"/tasks/{task_id}", headers=b).status_code == 404
    # The owner's task must still exist.
    assert client.get(f"/tasks/{task_id}", headers=a).status_code == 200