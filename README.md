# Task Tracker

A small Kanban-style task tracker: a FastAPI backend with an in-memory store, and
a vanilla-JS frontend (no build step, no framework).

Built as the Modules 1-3 project for the AI-Assisted Coding course, then extended
with two features (due dates + overdue filter, tags/labels) for the Mid-Course
Project Sprint. See [docs/midcourse/](docs/midcourse/) for the sprint documentation.

## Project structure

```
app/            FastAPI backend (models, storage, routes, business rules)
tests/          pytest suite + tests/verify_a.py model-verification script
frontend/       static Kanban board (index.html + app.js), no build step
docs/midcourse/ Mid-course project sprint documentation
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
python -m tests.verify_a      # 8 Pydantic model checks, prints PASS/FAIL
pytest tests/ -v               # full API test suite
```
