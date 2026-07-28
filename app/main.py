from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app import storage
from app.business_rules import validate_status_transition
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate) -> TaskResponse:
    return storage.add_task(payload)


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
) -> list[TaskResponse]:
    tasks = storage.get_all_tasks()
    if status is not None:
        tasks = [t for t in tasks if t.status == status]
    if priority is not None:
        tasks = [t for t in tasks if t.priority == priority]
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str) -> TaskResponse:
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def patch_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    existing = storage.get_task_by_id(task_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.status is not None:
        if not validate_status_transition(existing.status, payload.status):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status transition from {existing.status.value} to {payload.status.value}",
            )

    updated = storage.update_task(task_id, payload)
    assert updated is not None
    return updated


@app.delete("/tasks/{task_id}", status_code=204, response_class=Response)
def delete_task(task_id: str) -> Response:
    deleted = storage.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
