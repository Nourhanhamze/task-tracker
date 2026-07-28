from datetime import date, timedelta

FUTURE_DATE = (date.today() + timedelta(days=30)).isoformat()
PAST_DATE = (date.today() - timedelta(days=5)).isoformat()


# ---- Due dates + overdue filter -------------------------------------------------


def test_create_task_with_valid_due_date(client):
    r = client.post("/tasks", json={"title": "Plan launch", "due_date": FUTURE_DATE})
    assert r.status_code == 201
    assert r.json()["due_date"] == FUTURE_DATE
    assert r.json()["overdue"] is False


def test_create_task_with_invalid_due_date_format_returns_422(client):
    r = client.post("/tasks", json={"title": "Bad date", "due_date": "not-a-date"})
    assert r.status_code == 422


def test_task_with_past_due_date_is_overdue(client):
    r = client.post("/tasks", json={"title": "Late task", "due_date": PAST_DATE})
    assert r.status_code == 201
    assert r.json()["overdue"] is True


def test_done_task_with_past_due_date_is_not_overdue(client, created_task):
    tid = created_task["id"]
    client.patch(f"/tasks/{tid}", json={"due_date": PAST_DATE})
    client.patch(f"/tasks/{tid}", json={"status": "InProgress"})
    r = client.patch(f"/tasks/{tid}", json={"status": "Done"})
    assert r.status_code == 200
    assert r.json()["overdue"] is False


def test_update_due_date(client, created_task):
    r = client.patch(f"/tasks/{created_task['id']}", json={"due_date": FUTURE_DATE})
    assert r.status_code == 200
    assert r.json()["due_date"] == FUTURE_DATE


def test_filter_returns_only_overdue_tasks(client):
    client.post("/tasks", json={"title": "On time", "due_date": FUTURE_DATE})
    client.post("/tasks", json={"title": "Late", "due_date": PAST_DATE})
    client.post("/tasks", json={"title": "No due date"})

    r = client.get("/tasks", params={"overdue": "true"})
    assert r.status_code == 200
    titles = [t["title"] for t in r.json()]
    assert titles == ["Late"]


# ---- Tags / labels ----------------------------------------------------------------


def test_create_task_with_tags(client):
    r = client.post("/tasks", json={"title": "Fix bug", "tags": ["backend", "urgent"]})
    assert r.status_code == 201
    assert r.json()["tags"] == ["backend", "urgent"]


def test_create_task_rejects_empty_tag(client):
    r = client.post("/tasks", json={"title": "x", "tags": ["ok", "   "]})
    assert r.status_code == 422


def test_create_task_rejects_too_many_tags(client):
    r = client.post("/tasks", json={"title": "x", "tags": [f"t{i}" for i in range(11)]})
    assert r.status_code == 422


def test_update_tags(client, created_task):
    r = client.patch(f"/tasks/{created_task['id']}", json={"tags": ["design"]})
    assert r.status_code == 200
    assert r.json()["tags"] == ["design"]


def test_filter_by_tag(client):
    client.post("/tasks", json={"title": "A", "tags": ["frontend"]})
    client.post("/tasks", json={"title": "B", "tags": ["backend"]})

    r = client.get("/tasks", params={"tag": "frontend"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "A"


def test_tags_preserved_after_unrelated_update(client):
    created = client.post("/tasks", json={"title": "Keep tags", "tags": ["keep-me"]}).json()
    r = client.patch(f"/tasks/{created['id']}", json={"description": "new description"})
    assert r.status_code == 200
    assert r.json()["tags"] == ["keep-me"]
