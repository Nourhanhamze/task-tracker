# Release Evidence

## Baseline

- Branch: `final-project`
- Date: 2026-08-24
- Local app run command: `uvicorn app.main:app --reload --port 8000`
- `/health` result: `200` — `{"status":"ok","timestamp":"2026-08-24T19:45:27.959584+00:00"}`
- Frontend check: opened `frontend/index.html` via `python -m http.server 5500` in
  the `frontend/` directory, then a real browser tab pointed at
  `http://localhost:5500`. The board renders its three columns with correct
  empty states, and posting a task through the API (`POST /tasks`) and
  reloading shows it appear in the To Do column with an "Edit" button — the
  create/edit flow is intact.
- Test command: `python -m tests.verify_a && pytest tests/ -v`
- Test result: `verify_a` — 8/8 PASS, exit code 0. `pytest` — **42 passed**
  (33 from the mid-course sprint + 9 added while fixing the facilitator-
  reported null-update bug, merged onto this branch — see "Documentation
  claim-vs-reality log" below and `docs/final-ai-review.md`'s note on the
  one `app/` change made on this branch).

## CI evidence

- Workflow file: `.github/workflows/ci.yml`
- Latest run link: https://github.com/Nourhanhamze/task-tracker/actions/runs/32767955982
  — status **success**, branch `final-project`, commit `7839c5b`, ~15s.
  Confirmed live (not just claimed) by fetching that exact URL directly.
- Test command used by CI: `python -m tests.verify_a` then `pytest tests/ -v`
  (two separate steps, both must exit 0 for the job to pass).
- Shortcut check (read directly from `.github/workflows/ci.yml`, line by
  line): no `continue-on-error`, no `|| true`, no `--exit-zero`-style flag,
  pytest is never skipped, Python version is pinned to the exact string
  `"3.11"` (not `latest` or unpinned), and dependency installation is an
  explicit step (`pip install -r requirements.txt`) that runs before the
  test steps, not assumed/skipped. Triggers cover `push` on all branches
  and `pull_request` into `main`.
- Intentional red-run evidence (optional for this brief; already produced
  during Module 4-equivalent work): commit `d932a2f` deliberately disabled
  the status-transition check, pushed, and the CI badge for `final-project`
  read **failing**; commit `5b17c53` reverted it and the badge read
  **passing** again. Full write-up in the "CI: green → red → green" section
  of this same `docs/` folder's earlier verification pass (kept for
  reference, not duplicated here).

## Docker evidence

- Build command: `docker build -t task-tracker:dev .`
- Run command: `docker run --rm -d -p 8000:8000 --name tt-dev task-tracker:dev`
- `/health` check: **not run against a live container** — Docker is not
  installed in the environment this repository was built in (checked: no
  `docker` on `PATH`, no Docker Desktop install directory; a real install
  attempt via `winget install Docker.DockerDesktop --silent` was made and
  produced no working `docker` command after several minutes; `wsl
  --status` confirmed WSL2 also isn't installed. Both Docker Desktop and
  WSL2 need admin elevation and a system restart to fully initialize,
  which isn't achievable non-interactively here). Rather than fabricate
  `docker build`/`docker run`/`curl` output, this is recorded as an honest
  gap — **but it was not left as pure static reading either.** A
  filesystem-level simulation of what the multi-stage build actually
  produces was run for real:

  1. Replicated the builder stage exactly: `pip install --no-cache-dir
     --prefix=<isolated dir> -r requirements.txt` — succeeded, resolving
     fastapi/uvicorn/pydantic/pytest/httpx and their transitive deps into
     an isolated `site-packages` completely outside this project's own
     `venv/`.
  2. Replicated the runtime stage's file set exactly: copied *only*
     `app/` into an empty scratch directory — nothing else, matching
     `COPY app ./app` with no other `COPY` instructions.
  3. Started `uvicorn app.main:app --host 0.0.0.0 --port 8000` — the
     Dockerfile's literal `CMD`, no `--reload` — with `PYTHONPATH` pointed
     *only* at the isolated builder-stage packages, from *only* the
     scratch directory containing just `app/`. It started clean:
     `Application startup complete.`
  4. `curl http://localhost:8001/health` (port changed to avoid clashing
     with the real dev server) returned **`200`**, and a full
     `POST`/`GET /tasks` round-trip worked — proving the app genuinely
     runs end-to-end using nothing but what the image's `COPY`
     instructions would actually contain.

  This is real, run evidence for "does the dependency-install approach
  work" and "is `app/` alone sufficient to run the server," which is most
  of what a `docker build && docker run` would additionally confirm. What
  it does **not** cover: the actual Linux `python:3.11-slim` base image
  (this ran on Windows Python of the same version — package resolution
  matched, but OS-level behavior wasn't tested), the `USER app` /
  non-root permission enforcement (no container user namespace exists
  outside a real container runtime), and the `HEALTHCHECK` instruction
  itself (never executed by anything outside a container).
- Non-root check: `Dockerfile` creates a system group/user (`groupadd
  --system app && useradd --system --gid app --no-create-home app`) and
  declares `USER app` before `CMD`. **Declared, not verified live** — the
  filesystem simulation above cannot exercise Linux user/permission
  enforcement (that only exists inside a real container runtime), so the
  equivalent of `docker exec tt-dev whoami` printing `app` was still not
  run. This remains the one genuinely uncloseable gap without an actual
  container runtime.
- No-baked-secrets check: `.dockerignore` explicitly excludes `.env`,
  `.env.*`, `*.pem`, `*.key`, `.git`, `venv/`, `.venv/`, caches, and
  `tests/`/`docs/`/`README.md`/`*.md`. The `Dockerfile` only ever `COPY`s
  the `app/` directory into the image (never the full build context), so
  even if a stray `.env` existed at the repo root it would not be copied
  regardless of `.dockerignore`. Confirmed no `.env` file exists anywhere
  in the repo (`find . -iname ".env*"` — no matches) and no secret-shaped
  strings appear in any tracked file (`git grep` scan — see
  `docs/final-ai-review.md`'s security mini-review).

## Documentation claim-vs-reality log

| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| `POST /tasks` returns `201` | `curl -X POST /tasks -d '{"title":"x"}'` against the running app | Accurate | None |
| `GET/PATCH/DELETE /tasks/{id}` return `404` for a missing id, matching the docstrings | Compared `curl /openapi.json` to the actual route decorators | **Inaccurate** — the auto-generated OpenAPI schema didn't list `404` as a possible response for any of the three routes, even though the code raises it (FastAPI only auto-documents `response_model`'s success code plus Pydantic 422s, not manually-raised `HTTPException`s, unless told to) | Added `responses={404: {...}}` (and `422` on PATCH) to all three route decorators; re-checked `/openapi.json` before/after to confirm |
| `tests/verify_a.py` fails loudly (non-zero exit) when a model check fails, so CI can rely on it | Read the script, then ran it after temporarily neutering one check | **Inaccurate** — every check only ever printed `PASS`/`FAIL` to stdout; the script always exited `0` regardless, so a broken validator would show green in CI forever | Added a failure counter and `sys.exit(1)` when any check fails; confirmed the exit code flips to `1` on a deliberately broken check, then confirmed `0` again after restoring it |
| `PATCH /tasks/{id}` with an explicit `null` for a required field is rejected | Facilitator-reported finding on the mid-course submission (`title: null` → `200`, stored `None`); reproduced directly with `TestClient`, then probed every other `TaskUpdate` field the same way | **Inaccurate** — `title` (as reported) *and* `description`, `status`, `priority`, `tags` all silently accepted an explicit `null` and stored it, corrupting fields typed non-nullable on `TaskResponse`. `assignee`/`due_date` were correctly unaffected (genuinely nullable) | Fixed all five affected validators in `app/models.py` to reject explicit `null` (422) while still leaving an *omitted* field untouched; added `tests/test_null_updates.py` (9 tests); this is the one `app/` change made on this branch — explained fully in `docs/final-ai-review.md` per the "Protect app/ and frontend/" ground rule |
