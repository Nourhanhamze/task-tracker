# AGENTS.md — Task Tracker

Repo-level context for any AI coding agent (Claude Code, Codex, Cursor,
Copilot, etc.) working in this repository. Read this before making changes.

## Stack

- Python 3.11, FastAPI, Pydantic v2, Uvicorn
- Tests: pytest, httpx (via FastAPI's `TestClient`)
- Frontend: vanilla HTML/CSS/JS, no build step, no framework
- Storage: in-memory Python dict (`app/storage.py`) — intentional, see
  `docs/decisions/in-memory-task-storage.md`

## Run / test / verify commands

```bash
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash; venv\Scripts\activate on cmd/PowerShell
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000   # backend, http://localhost:8000, docs at /docs

cd frontend && python -m http.server 5500   # frontend, http://localhost:5500 (separate terminal)

python -m tests.verify_a   # 8 Pydantic model checks, prints PASS/FAIL
pytest tests/ -v            # full test suite
```

CI runs `pytest tests/ -v` on Python 3.11 for every push and PR to `main` —
see `.github/workflows/ci.yml`. Docker build/run commands are in `README.md`
and `docs/verification.md`.

## Architecture

```
app/
  models.py          Pydantic v2 request/response models, enums, validators
  storage.py          in-memory dict store + CRUD helpers (add_task, get_all_tasks,
                       get_task_by_id, update_task, delete_task, _reset)
  business_rules.py   status-transition rules, overdue computation
  main.py              FastAPI app, 5 CRUD routes + /health, CORS config
frontend/
  index.html           Kanban board markup + design-system CSS
  app.js                fetch/render logic, drag-and-drop, modal form
tests/
  verify_a.py           standalone Pydantic model verification script
  conftest.py            pytest fixtures (client, created_task, storage reset)
  test_tasks.py           baseline CRUD/validation/transition tests
  test_features.py        due-date/overdue and tags/labels tests
docs/                    project documentation (see README for the index)
```

## Business rules — do not guess these

- **Task fields:** `id`, `title`, `description`, `status`, `priority`,
  `assignee`, `due_date` (optional), `tags` (optional list), `overdue`
  (server-computed, never client-settable), `created_at`, `updated_at`.
- **Title:** required, trimmed, non-empty after trim, max 200 chars.
- **Status enum:** `ToDo`, `InProgress`, `Done` (exact casing matters — the
  frontend sends these exact strings).
- **Valid status transitions:** `ToDo → InProgress`, `InProgress → Done`,
  `Done → InProgress`. Everything else (including same-status, e.g.
  `InProgress → InProgress`) returns `422`. A missing task returns `404`
  *before* transition validation runs.
- **Tags:** each tag trimmed, rejected if empty after trim, max 10 tags per
  task, max 30 chars per tag.
- **Overdue:** `due_date` in the past AND `status != Done` → `overdue: true`.
  This is **recomputed on every read**, never persisted as a fixed value —
  see `docs/decisions/in-memory-task-storage.md` and the mid-course
  `docs/midcourse/mini-adr.md` for why.
- **Extra fields are rejected** (`extra="forbid"`) on `TaskCreate` and
  `TaskUpdate` — clients cannot set `id`, `created_at`, `updated_at`, or
  `overdue` directly.

## Frontend UI states

The board (`frontend/app.js`) has four states driven by `#status-banner`:
loading, error (fetch/PATCH failed), ready (normal), and per-column empty
placeholders when a column has zero tasks. Drag-and-drop sends `PATCH
/tasks/{id}` with the new status; a rejected move (422) reverts the board
via a full re-fetch, then shows the server's error message.

## CORS / local dev

Backend CORS (`app/main.py`) allows `http://localhost:5500`,
`http://127.0.0.1:5500`, `5173` variants — the frontend dev-server ports used
in this course. If you serve the frontend from a different port, add that
origin explicitly; do not switch to `allow_origins=["*"]`.

## Do-not rules

- Do not add authentication, user accounts, or a real database — out of
  scope for this course project (see Module 1 scope decisions).
- Do not add Docker/CI steps beyond what's asked (no deployment automation).
- Do not weaken CI to make it pass (no `continue-on-error`, `|| true`,
  `--exit-zero`, or floating `latest` version tags).
- Do not commit `.env` files, credentials, tokens, or real personal data.
- Do not implement the "comments" feature discussed in
  `docs/decisions/comments-feature-plan.md` — that document is a plan only.

## Review expectations for AI agents

- Cite the actual file and line for any claim about behavior — do not
  describe a generic FastAPI project.
- Prefer read-only analysis for review/security/planning/governance tasks;
  required outputs for those tasks live under `docs/`. Flag (don't silently
  make) any edit outside `docs/` during those tasks.
- Read the diff before proposing it as done. A generated artifact is not
  finished until it has been run/tested and the evidence is recorded.
