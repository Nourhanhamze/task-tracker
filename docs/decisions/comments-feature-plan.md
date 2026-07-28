# Comments Feature — Plan Only, Not Implemented

This document plans a task-comments feature two ways, critiques the
result, and compares them. **No code was written for this feature** — the
Module 5 boundary for this exercise is docs-only; `app/` was not touched.

Scope (fixed by the course brief): `id`, `task_id`, `author` (1-100 chars),
`body` (1-2000 chars), `created_at` (server UTC). Plan the
model/storage/API behavior, concrete tests, frontend behavior, and doc
updates — without implementing them.

## Plan A — generic (no repo access)

Asked for a comments-feature plan with no file context, just the field
list above. What it produced, roughly:

- A `Comment` SQLAlchemy model with a foreign key to `Task`, migrated with
  Alembic.
- `POST/GET/PUT/DELETE /comments` as a top-level resource with its own
  router file and pagination (`?page=&limit=`).
- Author identity resolved from a `current_user` auth dependency.
- Soft-delete (`deleted_at` column) instead of hard delete.
- Frontend described generically as "add a comments component that
  fetches and renders a list," with no reference to this project's actual
  fetch/render pattern or its vanilla-JS-no-framework constraint.
- Tests described as "add unit tests for the comment model and
  integration tests for the endpoints," with no concrete test names or
  cases.

None of this is unreasonable in the abstract — it's a normal way to build
a comments feature in a typical CRUD app with a real database and auth.
It is wrong for *this* repo on nearly every specific: there is no
database, no ORM, no auth, no pagination anywhere else in the API, and no
soft-delete pattern (`delete_task` hard-deletes). A plan this generic
would need a full rewrite before anyone could implement it here.

## Plan B — repo-grounded

Read `app/models.py`, `app/storage.py`, `app/main.py`,
`app/business_rules.py`, `tests/conftest.py`, `tests/test_tasks.py`,
`frontend/app.js`, `AGENTS.md`, and `README.md` before planning.

**Data model & storage.** Follow the existing `TaskCreate`/`TaskResponse`
split exactly: a `CommentCreate` model (`extra="forbid"`, `task_id` +
`author` + `body`, all required) and a `CommentResponse` model (adds
server-generated `id` via `new_task_id()`-style `uuid4().hex` and
`created_at` via `utc_now()`). Storage: a second module-level dict in
`app/storage.py` (or a new `app/comment_storage.py` mirroring the same
five-function shape: `add_comment`, `get_comments_for_task`,
`delete_comment`, `_reset`), keyed by comment id, consistent with
`docs/decisions/in-memory-task-storage.md`'s reasoning for not reaching
for a database.

**Validation.** `author`: trim, reject empty after trim, max 100 chars —
same shape as `_validate_title`. `body`: trim, reject empty after trim,
max 2000 chars — same shape, different limit. `task_id` must reference an
existing task; validated in the route (via `_get_task_or_404`), not in
the Pydantic model, matching how `patch_task` checks existence before
checking the transition rule.

**API routes.** Nested under the task, matching REST conventions already
implied by the existing single-resource routes:
- `POST /tasks/{task_id}/comments` → 201, 404 if task missing, 422 if
  `author`/`body` invalid.
- `GET /tasks/{task_id}/comments` → 200 list (empty list, not 404, if the
  task exists but has no comments — matching `GET /tasks`'s empty-list
  behavior), 404 if the task itself doesn't exist.
- `DELETE /tasks/{task_id}/comments/{comment_id}` → 204, 404 if the task
  or the comment doesn't exist.

**Tests.** New `tests/test_comments.py`, reusing the `client` and
`created_task` fixtures from `tests/conftest.py`: add comment (201), reject
blank/whitespace-only body (422), reject blank author (422), list comments
for a task (200, correct order), list comments for empty task (200, `[]`),
comment on nonexistent task (404), delete comment (204), delete missing
comment (404), delete comment on missing task (404).

**Frontend.** Extend the existing edit modal (`frontend/index.html` /
`app.js`) with a comments list + add-comment mini-form, reusing the
existing `fetch`/`escapeHtml`/error-banner patterns in `app.js` rather
than introducing new state-management machinery.

**Docs.** Add the new endpoints to `README.md`'s documentation index area
and to `AGENTS.md`'s business-rules section once implemented.

## Critique (Plan B, section by section)

| Section | Label | Why |
|---|---|---|
| Data model & storage | **Right** | Extends the existing dict-storage pattern with the same five-function shape instead of inventing a database — matches `docs/decisions/in-memory-task-storage.md`. |
| Validation | **Missing** | No maximum comment count per task. `docs/security-review.md` finding #2 found `description`/`assignee` unbounded and flagged it as a real, reproducible risk (2MB POST accepted). A comments feature makes the same mistake possible again in a new place (unbounded comments per task) unless a cap is decided now, not after it ships. |
| API routes | **Missing** | Doesn't decide what happens to a task's comments when the task itself is deleted (`DELETE /tasks/{id}`). Cascade-delete the comments? Leave them orphaned? This needs an explicit answer before implementation, not a default nobody chose on purpose. |
| Tests | **Right** | Concrete test names and cases, following this repo's existing naming convention (`test_<action>_<condition>_<expected_result>`), not "add tests for comments." |
| Frontend | **Needs-Resequencing** | The plan describes a "comment count badge on cards" as a frontend nice-to-have, but whether that count comes from `GET /tasks` returning an inline `comment_count` field or from the frontend making a second fetch per task is an **API design decision**, not a frontend implementation detail — it needs to be resolved during the "API routes" section above, not deferred to whoever builds the UI. |
| Docs | **Right** | Matches this project's actual pattern of updating `README.md`'s index and `AGENTS.md`'s business-rules section rather than a separate wiki or changelog this repo doesn't have. |

## Comparison

Plan A was fluent and would read as competent to someone who'd never seen
this repo — that's exactly the risk. Plan B caught two real open
decisions (comment count cap, cascade-delete behavior) that Plan A's
genericness couldn't have surfaced, because Plan A had no repo-specific
constraints to react to. A generic plan is still worth running first for
raw brainstorming breadth (Plan A's "soft-delete" idea is a legitimate
option even though it doesn't fit this repo yet), but only the
grounded-and-critiqued version is close to something I'd hand to a
teammate as an actual implementation plan.
