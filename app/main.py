"""FastAPI application: routes, CORS, and response post-processing.

Storage and validation live in app/storage.py and app/models.py; this
module wires HTTP routes to those layers and enforces status-transition
rules (app/business_rules.py) at the boundary.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app import storage
from app.business_rules import compute_overdue, validate_status_transition
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate

app = FastAPI(title="Task Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _with_overdue(task: TaskResponse) -> TaskResponse:
    """Return `task` with `overdue` recomputed against the current date.

    `overdue` is never trusted from storage: a task can become overdue
    purely because time passed, without anyone writing to it, so it must
    be recomputed on every read rather than persisted at write time.

    Args:
        task: A task as read from storage (its `overdue` field may be
            stale).

    Returns:
        The same task if the computed value already matches, otherwise a
        copy with `overdue` corrected.
    """
    overdue = compute_overdue(task.due_date, task.status)
    if overdue == task.overdue:
        return task
    return task.model_copy(update={"overdue": overdue})


def _get_task_or_404(task_id: str) -> TaskResponse:
    """Fetch a task by id or raise the standard 404.

    Args:
        task_id: The task's server-generated id.

    Returns:
        The matching task.

    Raises:
        HTTPException: 404 if no task with that id exists.
    """
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/health")
def health() -> dict:
    """Liveness check.

    Returns:
        dict: `{"status": "ok", "timestamp": <UTC ISO-8601 string>}`.
            Always HTTP 200; there is no failure path for this route.
    """
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate) -> TaskResponse:
    """Create a task.

    Args:
        payload: Validated task fields (title required; status/priority
            default to ToDo/Medium; due_date and tags optional).

    Returns:
        TaskResponse: The created task, HTTP 201.

    Raises:
        (FastAPI/Pydantic) 422 if `payload` fails model validation, e.g. a
            blank title, an unknown field, or an invalid tag/due_date -
            handled by FastAPI before this function runs.
    """
    return _with_overdue(storage.add_task(payload))


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    tag: Optional[str] = None,
    overdue: Optional[bool] = None,
) -> list[TaskResponse]:
    """List tasks, optionally filtered.

    Filters are combined with AND when more than one is given. An empty
    or no-match result is a normal 200 with `[]`, not an error.

    Args:
        status: Exact status match (`ToDo`, `InProgress`, `Done`).
        priority: Exact priority match (`Low`, `Medium`, `High`).
        tag: Case-insensitive match against any tag on the task.
        overdue: Filter to only overdue (`true`) or only non-overdue
            (`false`) tasks, computed fresh against the current date.

    Returns:
        list[TaskResponse]: Matching tasks, HTTP 200. Never raises.
    """
    tasks = [_with_overdue(t) for t in storage.get_all_tasks()]
    if status is not None:
        tasks = [t for t in tasks if t.status == status]
    if priority is not None:
        tasks = [t for t in tasks if t.priority == priority]
    if tag is not None:
        needle = tag.strip().lower()
        tasks = [t for t in tasks if needle in [x.lower() for x in t.tags]]
    if overdue is not None:
        tasks = [t for t in tasks if t.overdue == overdue]
    return tasks


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    responses={404: {"description": "Task not found"}},
)
def get_task(task_id: str) -> TaskResponse:
    """Fetch a single task by id.

    Args:
        task_id: The task's server-generated id.

    Returns:
        TaskResponse: The task, HTTP 200.

    Raises:
        HTTPException: 404 if the id does not exist.
    """
    return _with_overdue(_get_task_or_404(task_id))


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    responses={404: {"description": "Task not found"}, 422: {"description": "Invalid status transition"}},
)
def patch_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    """Partially update a task.

    Existence is checked before transition validation, so a missing task
    always returns 404 even if the payload also has an invalid status
    transition. Fields omitted from `payload` (not sent as `None`, simply
    absent) are left unchanged - see `storage.update_task`.

    Args:
        task_id: The task's server-generated id.
        payload: Fields to update. If `status` is included, it must be a
            valid transition from the task's current status (see
            `app.business_rules.VALID_TRANSITIONS`); same-status
            "updates" are rejected as no-ops.

    Returns:
        TaskResponse: The updated task, HTTP 200.

    Raises:
        HTTPException: 404 if the id does not exist; 422 if `status` is
            present and the transition is not in `VALID_TRANSITIONS`.
    """
    existing = _get_task_or_404(task_id)

    if payload.status is not None:
        if not validate_status_transition(existing.status, payload.status):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status transition from {existing.status.value} to {payload.status.value}",
            )

    updated = storage.update_task(task_id, payload)
    assert updated is not None
    return _with_overdue(updated)


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    response_class=Response,
    responses={404: {"description": "Task not found"}},
)
def delete_task(task_id: str) -> Response:
    """Delete a task.

    Args:
        task_id: The task's server-generated id.

    Returns:
        Response: Empty body, HTTP 204, on success.

    Raises:
        HTTPException: 404 if the id does not exist.
    """
    deleted = storage.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
