def test_create_task_returns_201(client):
    r = client.post("/tasks", json={"title": "Write report"})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Write report"
    assert body["status"] == "ToDo"
    assert body["priority"] == "Medium"
    assert body["id"]


def test_create_task_missing_title_returns_422(client):
    r = client.post("/tasks", json={})
    assert r.status_code == 422


def test_create_task_blank_title_returns_422(client):
    r = client.post("/tasks", json={"title": "   "})
    assert r.status_code == 422


def test_create_task_rejects_extra_field(client):
    r = client.post("/tasks", json={"title": "x", "made_up": "value"})
    assert r.status_code == 422


def test_list_tasks_empty_returns_200_and_empty_list(client):
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.json() == []


def test_list_tasks_filters_by_status(client):
    client.post("/tasks", json={"title": "A", "status": "ToDo"})
    r2 = client.post("/tasks", json={"title": "B", "status": "ToDo"})
    client.patch(f"/tasks/{r2.json()['id']}", json={"status": "InProgress"})

    r = client.get("/tasks", params={"status": "InProgress"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "B"


def test_list_tasks_filters_by_priority(client):
    client.post("/tasks", json={"title": "Low one", "priority": "Low"})
    client.post("/tasks", json={"title": "High one", "priority": "High"})

    r = client.get("/tasks", params={"priority": "High"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "High one"


def test_get_task_by_id_returns_200(client, created_task):
    r = client.get(f"/tasks/{created_task['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created_task["id"]


def test_get_task_missing_id_returns_404(client):
    r = client.get("/tasks/does-not-exist")
    assert r.status_code == 404


def test_patch_task_updates_title(client, created_task):
    r = client.patch(f"/tasks/{created_task['id']}", json={"title": "Updated title"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated title"


def test_patch_task_missing_id_returns_404(client):
    r = client.patch("/tasks/does-not-exist", json={"title": "x"})
    assert r.status_code == 404


def test_patch_task_invalid_payload_returns_422(client, created_task):
    r = client.patch(f"/tasks/{created_task['id']}", json={"priority": "Urgent"})
    assert r.status_code == 422


def test_valid_transition_todo_to_inprogress(client, created_task):
    r = client.patch(f"/tasks/{created_task['id']}", json={"status": "InProgress"})
    assert r.status_code == 200
    assert r.json()["status"] == "InProgress"


def test_valid_transition_inprogress_to_done(client, created_task):
    tid = created_task["id"]
    client.patch(f"/tasks/{tid}", json={"status": "InProgress"})
    r = client.patch(f"/tasks/{tid}", json={"status": "Done"})
    assert r.status_code == 200
    assert r.json()["status"] == "Done"


def test_invalid_transition_todo_to_done_returns_422(client, created_task):
    r = client.patch(f"/tasks/{created_task['id']}", json={"status": "Done"})
    assert r.status_code == 422


def test_invalid_transition_done_to_todo_returns_422(client, created_task):
    tid = created_task["id"]
    client.patch(f"/tasks/{tid}", json={"status": "InProgress"})
    client.patch(f"/tasks/{tid}", json={"status": "Done"})
    r = client.patch(f"/tasks/{tid}", json={"status": "ToDo"})
    assert r.status_code == 422


def test_same_status_transition_returns_422(client, created_task):
    tid = created_task["id"]
    client.patch(f"/tasks/{tid}", json={"status": "InProgress"})
    r = client.patch(f"/tasks/{tid}", json={"status": "InProgress"})
    assert r.status_code == 422


def test_title_only_update_skips_transition_validation(client, created_task):
    r = client.patch(f"/tasks/{created_task['id']}", json={"title": "No status change"})
    assert r.status_code == 200


def test_delete_existing_task_returns_204_no_body(client, created_task):
    r = client.delete(f"/tasks/{created_task['id']}")
    assert r.status_code == 204
    assert r.content == b""


def test_delete_missing_task_returns_404(client):
    r = client.delete("/tasks/does-not-exist")
    assert r.status_code == 404


def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
