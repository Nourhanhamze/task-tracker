# Architecture — Strategy B (Structured Context)

**Context given for this pass:** the full text of `AGENTS.md` (stack, run
commands, architecture map, business rules, UI states, CORS, do-not
rules), plus one-line-per-file summaries — not the raw file contents:

```
app/models.py        - Pydantic v2 models + enums + validators
app/storage.py         - in-memory dict CRUD helpers
app/business_rules.py   - status transitions + overdue logic
app/main.py               - FastAPI routes, CORS, response post-processing
frontend/index.html        - Kanban board markup + CSS design system
frontend/app.js              - fetch/render/drag-drop/modal logic
tests/verify_a.py              - 8 Pydantic model checks
tests/test_tasks.py              - baseline CRUD/validation/transition tests
tests/test_features.py             - due-date/overdue + tags tests
```

---

## System overview

A FastAPI backend with an in-memory dict store (not a database — see
`docs/decisions/in-memory-task-storage.md`) and a vanilla-JS Kanban
frontend, no build step. Tasks move through three statuses (ToDo,
InProgress, Done) with backend-enforced transition rules, and carry
priority, optional due date, and optional tags in addition to title/
description/assignee.

## Backend structure

Four files, each with one job (per AGENTS.md's architecture map):
`app/models.py` (data shape + validation), `app/storage.py` (persistence,
a module-level dict, five plain functions), `app/business_rules.py`
(status-transition legality + overdue computation, kept separate from
routing), and `app/main.py` (the five CRUD routes plus `/health`, CORS
config, and response post-processing like recomputing `overdue` before
every response).

## Frontend structure

`frontend/index.html` + `frontend/app.js`, no framework, no build step.
Fetches from `GET /tasks` (with optional status/priority/tag/overdue query
filters per AGENTS.md), renders three columns sorted by priority, and
supports drag-and-drop status changes (`PATCH /tasks/{id}`) plus a create/
edit modal.

## Data flow

Client → `TaskCreate`/`TaskUpdate` (validated, `extra="forbid"`, so unknown
fields are a 422) → route handler in `app/main.py` → `app/storage.py`
(persist) → `app/business_rules.py` (transition check on PATCH, overdue
recompute on every response) → `TaskResponse` → client re-renders from the
returned/refetched task list.

## Testing and verification

`tests/verify_a.py` for model-level checks (title trimming, extra-field
rejection, defaults), `tests/test_tasks.py` for the baseline CRUD/
transition-matrix behavior, `tests/test_features.py` for due-date/overdue
and tags. Per AGENTS.md, run commands are `python -m tests.verify_a` and
`pytest tests/ -v`.

## Known limits

Per AGENTS.md's do-not rules: no authentication, no real database, no
deployment automation beyond the CI test workflow — all explicit course-
scope decisions, not oversights. CORS is limited to a fixed local
dev-server origin allowlist.

---

## Self-assessment (for the comparison log)

More complete and accurate than Strategy A on every section — because
AGENTS.md already states the real stack, structure, and do-not rules
directly, this pass didn't have to guess. But it's also noticeably closer
to restating AGENTS.md in prose than adding new insight: the "Data flow"
section is the only part that required synthesizing across files rather
than paraphrasing the provided context. This is the "structured context
can improve completeness but produce longer, less original output" effect
the lecture calls out.
