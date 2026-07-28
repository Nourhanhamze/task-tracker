# Security Review

Read-only audit of the Task Tracker repository (`app/`, `tests/`,
`frontend/`, `requirements.txt`, `Dockerfile`, `.github/workflows/ci.yml`).
No files were edited as part of this review; findings below were confirmed
against the actual code, not accepted on the audit's word.

## AI findings table

| # | Finding | File / evidence | Grade | Reasoning |
|---|---|---|---|---|
| 1 | No authentication, authorization, or ownership checks on any `/tasks` endpoint — any client that can reach the API can create, read, update, or delete any task. | `app/main.py`, all five routes | **Valid** | Real for this codebase. Intentional for a learning project (see `AGENTS.md` do-not rules: "no authentication... unless explicitly approved"), but the production risk is real and worth naming precisely rather than hand-waving. |
| 2 | `description` and `assignee` fields have no maximum length, unlike `title` (200 chars) and `tags` (30 chars/10 tags). A client can submit an arbitrarily large string for either. | `app/models.py` `TaskCreate`/`TaskUpdate` — `description: str = ""`, `assignee: Optional[str] = None`, no `field_validator` for either | **Valid** | Reproduced directly: `POST /tasks` with a 2,000,000-character `description` and a 10,000-character `assignee` returned `201` and stored both in full. In this in-memory-dict project this is a memory-exhaustion / oversized-response risk, not a theoretical one. |
| 3 | CORS middleware allows all methods and all headers (`allow_methods=["*"]`, `allow_headers=["*"]`), even though `allow_origins` is a fixed, non-wildcard allowlist. | `app/main.py`, `CORSMiddleware` config | **Valid** (low severity) | Real configuration, but origins are explicitly enumerated (not `"*"`), so this is the kind of "acceptable for local development, document before deployment" case the audit prompt itself calls out — not urgent, but should be tightened (`allow_methods=["GET","POST","PATCH","DELETE"]`) before any real deployment. |
| 4 | Potential SQL injection in task filtering. | Audit tool's generic finding, no file cited | **False Positive** | This project has no SQL anywhere — `app/storage.py` is a plain Python dict with list-comprehension filtering. There is no query string to inject into. |
| 5 | Task ids are sequential/enumerable, allowing an attacker to guess other tasks' ids. | Audit tool's generic finding, no file cited | **False Positive** | Checked `app/models.py::new_task_id` — `uuid4().hex`, a 32-character random hex string, not sequential. Confirmed by creating three tasks in a row and observing unrelated ids. |
| 6 | "Validate all input more thoroughly." | Audit tool's generic finding, no file cited | **Noise** | True in the abstract, not actionable without naming a field, a route, or a concrete failure mode. (Finding #2 above is what this should have said.) |
| 7 | Docker container may run as root. | Generic Docker-security checklist item | **Valid, but already mitigated** | `Dockerfile` explicitly creates a non-root `app` user and runs `USER app` before `CMD`. Not verified against a live container in this environment (Docker isn't installed here — see `docs/verification.md`), so this is graded on the Dockerfile's declared configuration, not a confirmed running-container check. |

## My manual findings

Beyond re-checking every AI finding above against the actual files, I ran
two checks the audit prompt didn't produce on its own:

- **Secret scan.** `grep -rniE "api[_-]?key|secret|password|token|aws_access|private_key|-----BEGIN"` across
  `*.py`, `*.js`, `*.html`, `*.yml`, `*.md`, plus `find . -iname ".env*"`.
  No matches outside this review's own documentation text (which
  legitimately mentions the words "secret"/"token" while describing rules
  *against* committing them). No `.env` file exists anywhere in the repo.
- **Error leakage.** Sent a malformed (non-JSON) body to `POST /tasks`.
  Got a clean `422` with a structured Pydantic-style error
  (`{"detail": [{"type": "json_invalid", ...}]}`) — no raw stack trace, no
  internal file paths, no framework version leaked in the response body.

## Reconciliation

| Agreement | AI-only | You-only |
|---|---|---|
| No-auth on task endpoints is a real, named risk (#1) | Unbounded `description`/`assignee` (#2) — the AI's generic input-validation Noise (#6) gestured at this without naming it; I had to find the actual unvalidated fields myself | Secret scan across the whole repo, not just the files the audit prompt happened to mention |
| CORS wildcard methods/headers worth documenting (#3) | | Malformed-JSON error-leakage check |
| | | Confirmed the Docker non-root user via reading `USER app` in the Dockerfile, since no live container check was possible |

The **You-only** column is doing the real work here: the AI audit produced
one genuinely specific, reproducible finding (task ids aren't sequential —
correctly graded False Positive when it claimed the opposite) and mostly
generic risk categories. Turning "validate input" into "these two specific
fields, confirmed with a 2MB POST that returned 201" required actually
running something against the code.

## Top-3 backlog

1. **Add a max length to `description` and `assignee`** (finding #2). Same
   pattern already used for `title` (`_validate_title`) and `tags`
   (`_validate_tags`) in `app/models.py` — a reasonable default is 5,000
   characters for `description`, 100 for `assignee` (matching the course's
   own "comments" planning doc, which independently proposes a 1-100 char
   author field — see `docs/decisions/comments-feature-plan.md`).
   **Owner:** next available implementation session. **Not fixed in this
   review** per the Module 5 boundary (read-only review; code fixes are a
   separate, explicitly-scoped change).
2. **Tighten CORS `allow_methods`/`allow_headers`** from `"*"` to the exact
   verbs/headers the frontend actually sends (finding #3), before any
   deployment beyond localhost.
3. **Name the no-auth decision explicitly in a decision note** (finding
   #1) rather than only a one-line "do-not" rule in `AGENTS.md` — a future
   teammate deciding whether this project is safe to expose beyond
   localhost needs the full reasoning, not just the current state.
