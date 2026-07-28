# Architecture

Synthesized from `docs/architecture-A.md` (minimal context), `-B.md`
(structured context: AGENTS.md + file summaries), and `-C.md` (targeted
anchor files: `main.py`/`models.py`/`storage.py` only) — see those three
for the raw experiment and `docs/verification.md`-style honesty about what
each did and didn't get right.

## System overview

A small Kanban-style task tracker: a FastAPI backend with an in-memory
dict store (deliberately not a database — see
`docs/decisions/in-memory-task-storage.md`) and a vanilla-JS, no-build-step
frontend. Tasks move through three statuses (`ToDo`, `InProgress`, `Done`)
under backend-enforced transition rules, and carry priority, an optional
due date, and optional tags alongside title/description/assignee.

## Backend structure

Four files, one job each:

- **`app/models.py`** — Pydantic v2 models and enums. `TaskCreate`/
  `TaskUpdate` are client-input models with `extra="forbid"` (unknown
  fields are a 422, not silently dropped); `TaskResponse` is the
  API-facing shape, including the server-computed `overdue` field.
  Validators live here too: `_validate_title` (trim, reject empty, max 200
  chars) and `_validate_tags` (trim each, reject empty, max 10 tags × 30
  chars).
- **`app/storage.py`** — a single module-level `dict[str, TaskResponse]`
  with five plain functions (`add_task`, `get_all_tasks`,
  `get_task_by_id`, `update_task`, `delete_task`, plus test-only
  `_reset`). `add_task` builds the response from
  `**payload.model_dump()` rather than a hand-written field list, so newly
  added `TaskCreate` fields flow through automatically (this wasn't true
  in an earlier version — see `docs/verification.md`).
  `update_task` uses `model_dump(exclude_unset=True)`, which is what makes
  "update the title, keep the existing tags" work without resending them.
- **`app/business_rules.py`** — kept separate from routing so the actual
  rules are readable in one place: `VALID_TRANSITIONS` (a frozenset of
  legal `(current, new)` status pairs — same-status "transitions" are
  intentionally excluded) and `compute_overdue` (a pure function of
  `due_date`/`status`/an optional `today` override, never trusting a
  stored value).
- **`app/main.py`** — FastAPI app, CORS restricted to four local dev-server
  origins, five CRUD routes plus `/health`. `_with_overdue` recomputes the
  overdue flag on every response (create/list/get/patch) rather than
  trusting whatever's in storage, since it depends on the current date.
  `_get_task_or_404` centralizes the "fetch or 404" pattern shared by
  `get_task` and `patch_task`.

## Frontend structure

`frontend/index.html` + `frontend/app.js`. No framework, no build step.
Fetches `GET /tasks` (optional `status`/`priority`/`tag`/`overdue` query
filters), renders three priority-sorted columns with loading/empty/ready/
error states, and supports native HTML5 drag-and-drop for status changes
(`PATCH /tasks/{id}`, reverting via a full re-fetch on a rejected/422
move) plus a create/edit modal with client- and server-side validation.

## Data flow

```
Client request
  -> Pydantic validation (TaskCreate/TaskUpdate; 422 on failure)
  -> route handler (app/main.py)
  -> app/storage.py function
  -> [PATCH only] app/business_rules.validate_status_transition (422 if illegal)
  -> app/main._with_overdue (recomputes overdue via app/business_rules.compute_overdue)
  -> TaskResponse JSON
  -> frontend re-fetches and re-renders the board
```

## Testing and verification

`tests/verify_a.py` — 8 standalone Pydantic model checks, exits non-zero
on failure (fixed during the End-of-Course pass; previously always exited
0 — see `docs/verification.md`). `tests/conftest.py` — `client`,
`created_task` fixtures, and an autouse `_reset()` fixture so every test
starts from empty storage. `tests/test_tasks.py` (21 baseline tests) and
`tests/test_features.py` (12 tests for due dates/overdue and tags) — 33
total. CI (`.github/workflows/ci.yml`) runs both `verify_a.py` and
`pytest` on every push/PR to `main`, proven to actually fail on a broken
test (`docs/verification.md`), not just run.

## Known limits

No authentication, authorization, or ownership checks (intentional course
scope — see `AGENTS.md` and `docs/security-review.md` finding #1). No real
database — single-process, in-memory, state lost on restart
(`docs/decisions/in-memory-task-storage.md`). `description` and `assignee`
fields have no length limit, a real (if low-severity) risk documented in
`docs/security-review.md` finding #2. CORS is a fixed local-dev-origin
allowlist, not meant to be deployed as-is.

---

## Comparison log

| Question | Answer |
|---|---|
| Which strategy produced the most accurate file-level description? | **C (targeted).** Every specific claim (exact function names, `model_dump(exclude_unset=True)`, the `USER app`-equivalent precision) traces to a line in one of the three anchor files. |
| Which strategy invented the most / sounded generic? | **A (minimal).** Database, ORM, migrations, React frontend, auth — none of it is true for this repo; all of it is a plausible-sounding default for "a FastAPI task tracker" in general. |
| Which strategy was most honest about what it hadn't inspected? | **C.** Explicitly wrote "not visible from the files I read" four separate times (frontend, tests, the actual transition rules, the actual overdue rule) rather than filling gaps from outside knowledge. |
| Which output would help a new teammate fastest? | **B (structured),** for a first read — it's complete enough to orient someone without requiring them to already know which three files matter. C is more precise but requires already knowing to ask about `business_rules.py`, tests, and the frontend separately. |
| Which context strategy for security work, onboarding docs, or feature planning? | **C for security work** (precision and honest boundaries matter more than coverage when the cost of a wrong claim is high — see how `docs/security-review.md` graded the SQL-injection false positive). **B for onboarding docs** (completeness matters more than exhaustive precision for a first orientation). **B, feeding into a C-style file-read pass, for feature planning** — this is exactly what `docs/decisions/comments-feature-plan.md` did (AGENTS.md context, then explicit file reads before the grounded plan). |

**Context strategy rule:** For correctness-sensitive or narrow tasks
(security review, a specific bug, "what does this function actually do"),
use targeted anchor-file context and require the agent to say what it
didn't read; for broad first-pass orientation (onboarding, architecture
overviews, initial feature brainstorming), structured context (a project
memory file plus file summaries) gets useful completeness faster than
either extreme.
