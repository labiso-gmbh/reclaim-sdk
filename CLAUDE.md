# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Unofficial Python SDK for the Reclaim.ai API (reverse-engineered from the web app + partial Swagger spec at `https://api.app.reclaim.ai/swagger/reclaim-api-0.1.yml`). Distributed on PyPI as `reclaim-sdk`. Version lives in `reclaim_sdk/__init__.py` (single source — `setup.py` reads it via regex).

Covers Tasks, DailyHabits, Hours (full CRUD on `/api/timeschemes` — custom working-hour profiles), Webhooks, Changelog. Many other Reclaim resources (Events, Calendars, Smart Habits/Meetings, Scheduling Links, etc.) remain unimplemented — see README "Not covered".

## Common commands

```bash
pip install -e ".[dev]"          # editable install + flake8/black
python examples/task_management.py   # smoke test (needs RECLAIM_TOKEN)
black reclaim_sdk                    # format
flake8 reclaim_sdk                   # lint
python setup.py sdist bdist_wheel    # build (CI does this on push to master)
```

No test suite. CI (`.github/workflows/publish-to-pypi.yml`) auto-publishes to PyPI on every push to `master` using `PYPI_TOKEN` secret — **bump `__version__` before merging or publish fails**.

## Architecture

Three layers:

1. **`ReclaimClient`** (`reclaim_sdk/client.py`) — singleton `httpx.Client` wrapper. `__new__` returns shared instance; `configure(token=...)` overrides config and re-initializes. Token resolves from `configure()` arg → `RECLAIM_TOKEN` env var. `request()` translates HTTP status codes to typed exceptions (401→`AuthenticationError`, 404→`RecordNotFound`, 400/422→`InvalidRecord`, else→`ReclaimAPIError`). Datetimes serialize as Zulu ISO via custom JSON encoder.

2. **`BaseResource`** (`reclaim_sdk/resources/base.py`) — Pydantic v2 model with `ENDPOINT` ClassVar. Generic CRUD: `get(id)`, `list(**params)`, `save()` (POST if no id, PATCH if id), `delete()`, `refresh()`. `save()` round-trips response back into `self.__dict__` so server-assigned fields populate.

3. **Resources** — subclass `BaseResource`, set `ENDPOINT`, declare fields with `alias=` for camelCase API names (Pydantic serializes `by_alias=True` in `to_api_data`).

### Task resource specifics (`resources/task.py`)

- **Time chunks = 15 min**. API speaks chunks; SDK exposes `duration` / `min_work_duration` / `max_work_duration` as float hours via properties that multiply/divide by 4. Keep this abstraction when adding time-related fields.
- **Planner actions** hit `/api/planner/*` (not `/api/tasks/*`): `start`, `stop`, `mark_complete` (→ `done`), `mark_incomplete` (→ `unarchive`), `add_time`, `log_work`, `prioritize`, `clear_exceptions`. Responses wrap payload under `taskOrHabit`.
- `log_work` requires Zulu format truncated to millisecond precision (`isoformat()[:-9] + "Z"`) — the API rejects full microseconds.
- `up_next` is an alias-property for `on_deck` (`onDeck` in API).
- Enums: `TaskPriority` (P1–P4), `TaskStatus`, `EventCategory`, `EventColor`.

### Adding a new resource

Follow `Task` pattern: subclass `BaseResource`, set `ENDPOINT`, use `Field(alias="camelCase")` for API field names, override `model_config` only if alias handling needs to differ (see `Hours` which disables auto-aliasing). Custom action methods call `self._client.post(...)` directly and feed response through `from_api_data`. Reference network tab in the browser for undocumented payloads — Swagger spec is incomplete.

## Conventions

- Python ≥3.7 officially supported (setup.py classifiers), but `int | None` syntax in `base.py` requires ≥3.10 in practice.
- No `Co-Authored-By` or AI attribution in commits/PRs/code (per global user rules).
