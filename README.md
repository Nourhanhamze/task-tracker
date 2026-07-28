# Task Tracker

A small Kanban-style task tracker: a FastAPI backend with an in-memory store, and
a vanilla-JS frontend (no build step, no framework).

Built across the AI-Assisted Coding course: Modules 1-3 (backend + frontend),
the Mid-Course Sprint (due dates + overdue filter, tags/labels — see
[docs/midcourse/](docs/midcourse/)), and the End-of-Course release-readiness
pass (CI, Docker, docs, security/governance review — see
[docs/](docs/) and [docs/decisions/](docs/decisions/)).

See [AGENTS.md](AGENTS.md) for the repo-level context AI coding agents should
read before making changes here.

## Features

- Kanban board (To Do / In Progress / Done) with priority-sorted cards,
  drag-and-drop status updates, and a create/edit modal.
- Status transitions are enforced by the backend (`app/business_rules.py`),
  not just hidden in the UI.
- **Due dates + overdue filter**: optional `due_date` on a task; cards past
  their due date (and not Done) show a red "Overdue" pill; toolbar checkbox
  filters the board to overdue tasks only; `GET /tasks?overdue=true`.
- **Tags/labels**: optional `tags` list per task (max 10 tags, 30 chars
  each, empty tags rejected); shown as chips on cards; toolbar text box
  filters by tag (case-insensitive); `GET /tasks?tag=<name>`.

## Project structure

```
app/                  FastAPI backend (models, storage, routes, business rules)
tests/                pytest suite + tests/verify_a.py model-verification script
frontend/              static Kanban board (index.html + app.js), no build step
.github/workflows/     CI (GitHub Actions): runs verify_a.py + pytest on push/PR
Dockerfile, .dockerignore   multi-stage, non-root container build
docs/midcourse/        Mid-course project sprint documentation
docs/decisions/         technical decision notes (ADR-style)
docs/                    end-of-course docs: security review, governance,
                         architecture, AI usage rules, playbook (see index below)
```

## Run the backend

```bash
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API root: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Open the frontend

The frontend is static HTML/JS and talks to the API at `http://localhost:8000`.
Serve it with any static file server so `fetch()` calls aren't blocked by
file:// restrictions, e.g.:

```bash
cd frontend
python -m http.server 5500
```

Then open http://localhost:5500 in a browser. The backend's CORS config
already allows `http://localhost:5500` and `http://127.0.0.1:5500`. If you
serve the frontend from a different port, add that origin to the
`allow_origins` list in `app/main.py`.

## Run the tests

```bash
python -m tests.verify_a      # 8 Pydantic model checks, prints PASS/FAIL, exits non-zero on failure
pytest tests/ -v               # full API test suite (33 tests)
```

## Run in Docker

```bash
docker build -t task-tracker:dev .
docker run --rm -d -p 8000:8000 --name tt-dev task-tracker:dev
curl -i http://localhost:8000/health
docker exec tt-dev whoami        # expect: app (not root)
docker stop tt-dev
```

The image is a multi-stage build (`Dockerfile`): a builder stage resolves
Python dependencies, and the runtime stage is `python:3.11-slim`, runs as a
non-root `app` user, and only contains `app/` (not `frontend/`, `tests/`, or
`docs/` — see `.dockerignore`). **Note:** this was written and verified by
static inspection against the Module 4 checklist in an environment without
Docker installed; see [docs/verification.md](docs/verification.md) for
exactly what was and was not run.

## CI

`.github/workflows/ci.yml` runs `python -m tests.verify_a` and `pytest tests/ -v`
on Python 3.11 for every push and pull request to `main`. No
`continue-on-error`, no `|| true`, no floating Python version — a failing
test fails the workflow. See [docs/verification.md](docs/verification.md)
for green → red → green proof (a deliberately broken test was pushed,
confirmed to fail CI, then reverted).

## Project conventions

- Status enum values are exact strings: `ToDo`, `InProgress`, `Done` (not
  `"To Do"` — that's only a display label in the frontend).
- Client input models (`TaskCreate`, `TaskUpdate`) use `extra="forbid"` —
  unknown fields are a `422`, not silently ignored.
- Server-managed fields (`id`, `created_at`, `updated_at`, `overdue`) are
  never accepted from a client payload.
- New task fields should flow through `storage.add_task` automatically via
  `payload.model_dump()` — do not hand-list fields there (see the fix in
  the Mid-Course-era `storage.py` history for why that broke once already).

## Documentation index

| Doc | What it's for |
|---|---|
| [AGENTS.md](AGENTS.md) | Repo context for AI coding agents |
| [docs/midcourse/](docs/midcourse/) | Mid-course feature sprint (due dates, tags) |
| [docs/decisions/](docs/decisions/) | Technical decision notes |
| [docs/verification.md](docs/verification.md) | CI, Docker, and claim-vs-reality evidence |
| [docs/review-log.md](docs/review-log.md) | AI-assisted code review, triaged Useful/Noise/Wrong |
| [docs/security-review.md](docs/security-review.md) | AI + manual security findings, graded and reconciled |
| [docs/governance-worksheet.md](docs/governance-worksheet.md) | What was shared with/received from AI, risk-classified |
| [docs/ai-usage.md](docs/ai-usage.md) | Concrete AI-usage rules for this project |
| [docs/architecture.md](docs/architecture.md) | System architecture (+ `architecture-A/B/C.md` context-strategy experiment) |
| [docs/ai-playbook.md](docs/ai-playbook.md) | Personal AI playbook and tool-choice Decision Card |
