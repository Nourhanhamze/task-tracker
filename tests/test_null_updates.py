"""Regression tests for explicit-null PATCH payloads.

Facilitator finding on the Mid-Course submission: sending an explicit
null for `title` in a PATCH was accepted with 200 and stored the invalid
value, letting a task end up with no title - uncovered by any test.

The same bug affected description/status/priority/tags too (any
TaskUpdate field that is NOT nullable on TaskResponse but had no guard
against an explicit null value). assignee/due_date are genuinely
nullable on TaskResponse, so null is a legitimate "clear this field"
value for those two and must keep working.
"""

import pytest


@pytest.mark.parametrize("field,null_payload", [
    ("title", {"title": None}),
    ("description", {"description": None}),
    ("status", {"status": None}),
    ("priority", {"priority": None}),
    ("tags", {"tags": None}),
])
def test_explicit_null_rejected_for_non_nullable_fields(client, created_task, field, null_payload):
    r = client.patch(f"/tasks/{created_task['id']}", json=null_payload)
    assert r.status_code == 422

    # the field must not have been corrupted - re-fetch and confirm it
    # still holds its original, valid value.
    refetched = client.get(f"/tasks/{created_task['id']}").json()
    assert refetched[field] is not None


def test_explicit_null_title_does_not_get_stored(client, created_task):
    r = client.patch(f"/tasks/{created_task['id']}", json={"title": None})
    assert r.status_code == 422

    refetched = client.get(f"/tasks/{created_task['id']}").json()
    assert refetched["title"] == created_task["title"]


def test_explicit_null_assignee_clears_it(client):
    created = client.post("/tasks", json={"title": "x", "assignee": "Sam"}).json()
    r = client.patch(f"/tasks/{created['id']}", json={"assignee": None})
    assert r.status_code == 200
    assert r.json()["assignee"] is None


def test_explicit_null_due_date_clears_it(client):
    created = client.post("/tasks", json={"title": "x", "due_date": "2030-01-01"}).json()
    r = client.patch(f"/tasks/{created['id']}", json={"due_date": None})
    assert r.status_code == 200
    assert r.json()["due_date"] is None


def test_omitting_a_field_still_leaves_it_unchanged(client, created_task):
    """Confirms the fix didn't turn 'field omitted' into a rejection too."""
    r = client.patch(f"/tasks/{created_task['id']}", json={"description": "only this changed"})
    assert r.status_code == 200
    assert r.json()["title"] == created_task["title"]
    assert r.json()["description"] == "only this changed"
