# Architecture — Strategy A (Minimal Context)

**Method note (read this first):** the Module 5 exercise assumes each
strategy runs in a fresh AI thread with no memory of the codebase. I built
this entire repository in this same continuous session, so I cannot be
genuinely "blind" to it the way a fresh thread would be — my own memory is
already repo-grounded. To make this comparison meaningful anyway, this
document was written under a hard self-imposed constraint: no file reads,
no repo-specific facts, answering only from the one-line prompt below, and
staying at the level of generality a model with zero project memory would
actually produce. Treat this as a disciplined simulation, not a claim of
true blindness — that honesty is itself the point of recording the method.

**Prompt used:** *"Write a one-page architecture document for a Task
Tracker REST API built with Python and FastAPI."*

---

## System overview

A Task Tracker is typically a small CRUD service: clients create, list,
update, and delete tasks through a REST API. A common shape is a FastAPI
app backed by a relational database (PostgreSQL is a frequent default),
accessed through an ORM such as SQLAlchemy or SQLModel, with Alembic
handling schema migrations.

## Backend structure

A conventional layout separates `models` (ORM/Pydantic schemas), `crud` or
`services` (business logic), and `routers` (HTTP endpoints), often with a
`database.py` for the DB session/engine setup. Tasks likely have fields
like `id`, `title`, `description`, `status`, and `priority`, with an enum
or foreign-key lookup table for status values.

## Frontend structure

Could be a single-page app (React/Vue) calling the API over `fetch`/axios,
or a server-rendered template. Without more context, either is plausible;
a React SPA is a common default assumption for a "task tracker" demo.

## Data flow

A typical request: client sends JSON → FastAPI validates via a Pydantic
schema → a service/CRUD layer writes to the database → the ORM model is
serialized back to a response schema → client re-fetches or receives the
updated object directly.

## Testing and verification

Likely pytest with a test database (SQLite in-memory or a Dockerized
Postgres), FastAPI's `TestClient`, and possibly fixtures for auth tokens
if the API requires authentication.

## Known limits

Unknown without more information: whether the API has authentication,
what the exact status values are, whether there's a frontend in this repo
at all, what the persistence layer actually is, and what, if any,
deployment or CI setup exists.

---

## Self-assessment (written with full repo knowledge, for the comparison log)

Almost everything above except the very top-level shape ("FastAPI, tasks
have a status/priority, CRUD over REST") is wrong for this specific repo:
there is no database, no ORM, no migrations, no auth, and the frontend is
vanilla JS, not React. The enum/status guess is coincidentally close
(this repo does use an enum) but the field list, storage layer, and
frontend assumption are all invented defaults, not repo facts.
