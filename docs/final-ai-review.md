# Final AI Review and Ownership Evidence

## The one `app/` change made on this branch

Per the ground rule "Protect app/ and frontend/: only change app/ or
frontend/ for a small bug fix, security fix, or documentation-supported
correction" — this branch has exactly one such change, and it's explained
here as required.

**What:** `app/models.py`'s `TaskUpdate` validators for `title`,
`description`, `status`, `priority`, and `tags` now reject an explicit
`null` value (422) instead of silently accepting it and letting it
overwrite a field that `TaskResponse` declares non-nullable.

**Why:** the facilitator grading the mid-course submission found that
`PATCH {"title": null}` returned `200` and stored an invalid `null`
title, uncovered by any test. Reproducing it and checking every other
`TaskUpdate` field the same way found the identical bug on four more
fields (`description`, `status`, `priority`, `tags`); `assignee`/
`due_date` were correctly unaffected since they're genuinely nullable.
This is a bug fix, exactly the category this ground rule permits.

**Evidence:** reproduced first (before writing any fix), fixed on
`mid-course-project`, verified Pydantic v2's actual validator-skip-on-
omitted-field behavior with a standalone script before relying on it (to
avoid breaking every other partial-update test), added 9 regression
tests (`tests/test_null_updates.py`), ran a Break Test (reverted the fix,
confirmed exactly the 6 relevant tests failed and 3 unrelated ones
didn't, restored it), then merged onto `final-project`. Full before/after
detail in `docs/midcourse/verification.md` and `docs/release-evidence.md`.

## AGENTS.md guardrails

- Repo-specific stack and commands included: **yes** — Python 3.11/
  FastAPI/Pydantic v2/pytest, exact `uvicorn`/`pytest`/`docker` commands.
- Docs-first/read-first guardrail included: **yes** — checked the actual
  heading, it's called "Review expectations for AI agents," not "Module 5
  boundaries" (an earlier draft of this section cited the wrong heading
  name and was corrected after re-reading `AGENTS.md` directly, exactly
  the kind of claim-vs-reality check this document is supposed to model):
  "Prefer read-only analysis for review/security/planning/governance
  tasks; required outputs for those tasks live under `docs/`. Flag (don't
  silently make) any edit outside `docs/` during those tasks."
- Unexpected app/frontend edits rule included: **yes** — same section,
  plus the separate "Do-not rules" heading (no auth/database/deployment scope creep
  without explicit approval).

## AI code review mini-log

Diff reviewed: commit `47e9cfe` (frontend design-system redesign, +332/-83
across two files) — chosen because it's a real, substantial diff, not a
toy example. Full six-finding log in `docs/review-log.md`; three
representative entries:

| AI comment | Grade | Reason | Verification or decision |
|---|---|---|---|
| No fallback declared for `color-mix()`/`backdrop-filter` (7 uses) — unsupported browsers could render the header with no background at all | **Useful** | Concrete, file-specific, real (if minor) risk | Accepted as a known limitation for this course project's evergreen-browser scope; documented, not fixed |
| "Renaming `--card-bg` to `--surface` risks breaking any file still referencing the old name" | **Wrong** | Sounds like due diligence but is wrong once checked | Ran `grep -rn "card-bg" frontend/` — zero matches anywhere in the repo; nothing to break |
| `-webkit-font-smoothing: antialiased` is a non-standard, engine-specific property | **Noise** | Technically true, inert on unsupported engines, zero risk | No action taken |

## AI security mini-review

Read-only audit against `app/`, `tests/`, `frontend/`, `requirements.txt`,
`Dockerfile`, `.github/workflows/ci.yml`. Full seven-finding log in
`docs/security-review.md`; three representative entries:

| Finding | File evidence | Grade | Reason | Next action |
|---|---|---|---|---|
| `description`/`assignee` fields have no maximum length | `app/models.py` — `title`/`tags` have length limits, `description`/`assignee` don't | **Valid** | Reproduced directly: a `POST /tasks` with a 2,000,000-character `description` and a 10,000-character `assignee` returned `201` and stored both in full | Logged in the security review's top-3 backlog; not fixed in this pass (out of scope for a read-only review per Module 5 boundaries) |
| Potential SQL injection in task filtering | Audit tool's generic finding, no file cited | **False Positive** | This project has no SQL anywhere — `app/storage.py` is a plain Python dict with list-comprehension filtering | None |
| Task ids are sequential/enumerable | Audit tool's generic finding, no file cited | **False Positive** | `app/models.py::new_task_id` uses `uuid4().hex` — checked directly, confirmed non-sequential by creating three tasks in a row | None |

## Manual security check

Two checks run independently of the AI audit's own suggestions:

- **Secret scan.** `grep -rniE "api[_-]?key|secret|password|token|aws_access|private_key|-----BEGIN"`
  across every tracked `*.py`/`*.js`/`*.html`/`*.yml`/`*.md` file, plus
  `find . -iname ".env*"`. No matches outside this review's own
  documentation text describing the rule against committing secrets — no
  actual secret, token, or `.env` file exists anywhere in the repository.
- **Error leakage.** Sent a malformed (non-JSON) body to `POST /tasks`.
  Got a clean `422` with a structured Pydantic-style error, no raw stack
  trace, no internal file path, nothing framework-version-identifying in
  the response body.

## One AI output I rejected or corrected

While writing `docs/decisions/in-memory-task-storage.md`, an early draft
suggested introducing a `StorageBackend` protocol/interface now, "so a
future database swap would be clean." I rejected this: there is exactly
one storage backend in this codebase and has been for the entire course.
An interface with a single implementation isn't abstraction, it's
indirection with no second caller to justify it — YAGNI, not engineering
discipline. The decision note keeps the plain dict and records the
rejected alternative explicitly rather than silently dropping it.

## Three AI usage rules

(Full list with reasoning in `docs/ai-usage.md`; three here:)

1. **Never paste:** `.env` files, API keys, tokens, passwords, or any
   credential, regardless of environment — and never real customer/
   personal data or production logs.
2. **Always verify:** before accepting any AI-written validation,
   business-rule, or status-code claim, run the actual request against
   the actual code. This exact category of mistake caused both the
   `storage.add_task` field-dropping bug (mid-course) and the
   `verify_a.py` always-exits-0 bug (this branch) — both looked correct
   on read and were wrong on run.
3. **Record AI contributions:** every commit states what was generated,
   what changed after review, and what was run to verify it. Every AI
   review/audit pass produces a graded log (Useful/Noise/Wrong or Valid/
   False Positive/Noise), never a raw, ungraded list.

## Ownership statement

I'm comfortable submitting this repo as my own work because every claim
in it traces to something I actually ran, not something an AI tool merely
asserted: the CI green→red→green proof came from watching real GitHub
Actions runs change status, not from reading a YAML file and assuming it
worked; the null-update fix came from reproducing the facilitator's exact
scenario myself before touching any code, then checking whether the same
bug existed elsewhere instead of patching only the reported symptom; the
Docker section says plainly that no live container was ever run, instead
of writing `docker exec` output that never happened. Where I accepted an
AI suggestion, I can point to the command or test that confirmed it
(`_get_task_or_404`, the `payload.model_dump()` fix); where I rejected
one, I can explain why in my own words (the `StorageBackend` protocol,
the "compute overdue once at write time" design). That's the standard I
held every piece of this repo to, not just the parts a grader is likely
to check closely.
