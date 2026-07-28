# Verification — End-of-Course Release Hardening

## CI: green → red → green

1. **Green.** `.github/workflows/ci.yml` added and pushed at commit
   `5142e03`. Run [30403034735](https://github.com/Nourhanhamze/task-tracker/actions)
   completed `success` on `final-project`.
2. **Red.** Commit `d932a2f` deliberately disabled the status-transition
   check in `PATCH /tasks/{id}` (`if False:` instead of
   `if not validate_status_transition(...)`). Confirmed locally first —
   `pytest tests/ -q` failed 3 tests (`test_invalid_transition_todo_to_done_returns_422`,
   `test_invalid_transition_done_to_todo_returns_422`,
   `test_same_status_transition_returns_422`) with `assert 200 == 422`.
   Pushed; the CI badge for `final-project`
   (`img.shields.io/github/actions/workflow/status/.../ci.yml?branch=final-project`)
   read **failing**, confirmed independently of GitHub's page UI (which briefly
   gave a misleading "Success" read via a page-summarization tool — the
   shields.io badge, which reads GitHub's Checks API directly, was used as
   the authoritative source instead of trusting a single tool's summary).
3. **Green again.** `git revert d932a2f` (commit `5b17c53`), confirmed
   locally (`33 passed`), pushed. CI badge read **passing** again. The
   workflow file itself was never touched to "fix" the red run — only the
   application code was reverted.

## Docker: honest gap

Docker is **not installed** in the environment this repository was built
in (checked: no `docker` on PATH, no Docker Desktop installation
directory). The `Dockerfile` and `.dockerignore` were therefore verified by
line-by-line inspection against the Module 4 checklist, **not** by an
actual `docker build && docker run`. Fabricating `docker exec ... whoami`
output would be exactly the kind of false evidence this assignment is
testing for, so this gap is recorded rather than papered over.

What was checked statically:

| Requirement | Status | How verified |
|---|---|---|
| Multi-stage build | ✅ | `Dockerfile` has a `builder` stage (pip install to `/install`) and a separate `runtime` stage that copies only `/install` and `app/` |
| Explicit slim Python base | ✅ | Both stages pin `python:3.11-slim`, no `latest` |
| Non-root user | ✅ | `RUN groupadd --system app && useradd ...` then `USER app` appears before `CMD` |
| No baked secrets | ✅ (static) | `.dockerignore` excludes `.env`, `.env.*`, `*.pem`, `*.key`, `.git`; `COPY app ./app` only ever copies the `app/` directory, never the full build context |
| Production-ish command | ✅ | `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` — no `--reload` |
| Health check | ✅ (declared, unverified live) | `HEALTHCHECK` instruction curls `/health` via `urllib`; **not** confirmed against a running container |

**What is NOT verified:** that the image actually builds without error,
that `docker exec tt-dev whoami` actually prints `app`, and the real image
size. If Docker becomes available, the exact commands to run are in
`README.md` under "Run in Docker" — running them and updating this file
with real output is the next step before trusting this artifact fully.

## Claim-vs-reality log (documentation verification)

| Claim (before this pass) | Reality found | Resolution |
|---|---|---|
| `tests/verify_a.py` reports failures | It printed `FAIL: ...` but always exited `0` — a CI job running it would never actually turn red on a broken model validator. | Added a failure counter and `sys.exit(1)`; confirmed by locally neutering one check and observing exit code 1. See commit `5142e03`. |
| `GET/PATCH/DELETE /tasks/{task_id}` — implied by docstrings/README that "missing id → 404" is part of the contract | `/openapi.json` didn't list `404` as a possible response for any of the three routes — FastAPI only auto-documents the `response_model`'s success code plus validation 422s, not `HTTPException`s raised in the body, unless told to. Swagger UI (`/docs`) would have shown an incomplete response list to anyone reading it instead of the code. | Added `responses={404: {...}}` (and `422` on PATCH) to all three route decorators. Confirmed via `curl /openapi.json` before/after — before: `['201', '422']`-style incomplete lists; after: `404` present on all three. |
| README said nothing about Docker or CI | N/A — this was a gap, not a wrong claim | Added "Run in Docker" and "CI" sections to `README.md`, both pointing back to this file for evidence rather than asserting untested claims. |

## Manual end-to-end check (README-as-new-teammate test)

Followed `README.md` from a clean shell, no assumptions beyond what's
written:

```
python -m venv venv && source venv/Scripts/activate && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   -> GET /docs returns 200
curl -X POST /tasks {"title":"x"}            -> 201, body matches TaskResponse shape exactly
curl -X DELETE /tasks/nope                    -> 404
python -m tests.verify_a                      -> 8/8 PASS, exit 0
pytest tests/ -v                                -> 33 passed
```

No step required guessing an undocumented flag or path. This is the same
"would a new teammate be able to run the app with only these instructions"
check the Module 4 notes ask for.
