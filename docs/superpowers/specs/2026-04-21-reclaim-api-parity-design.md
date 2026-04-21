# reclaim-sdk 0.7.0 — API Parity Design

**Date:** 2026-04-21
**Author:** Laurence Labusch
**Status:** Approved (brainstorming phase)

## Goal

Bring `reclaim-sdk` up to parity with the current public Swagger at `https://api.app.reclaim.ai/swagger/reclaim-api-0.1.yml`. Eight deliverables: bug fix, Task schema alignment, new Task endpoints, new task-planner actions, required `user` query param, Webhooks resource, full Habits resource (incl. templates), Changelog endpoints. Version bump `0.6.4` → `0.7.0`. Breaking changes allowed.

## Decisions (from brainstorming)

| # | Decision |
|---|---|
| Scope | All 8 items in one release |
| Test infra | `pytest` + `respx` (mocked) + optional live mode behind `RECLAIM_LIVE_TEST=1` |
| Breaking changes | Full break — no legacy aliases, no backwards-compat shims |
| Webhooks | CRUD + typed pydantic payload models + signature-verification helper |
| Habits | Full (CRUD + planner actions + templates + `migrate-to-smart-series`) |
| TDD ordering | Vertical slice per endpoint (red/green/refactor one at a time) |
| Live-mode isolation | Single `RECLAIM_TOKEN` + UUID-prefixed entities + aggressive teardown |
| Code sharing | Mixins mirroring Reclaim's trait model (`Snoozeable`, `StartStoppable`, …) |

## Architecture

### Layers

1. **`ReclaimClient`** — singleton `httpx.Client` wrapper (unchanged core). Adds `current_user()` method: lazy `GET /api/users/current`, cached on instance. Cache invalidated on `configure()`.
2. **`BaseResource`** — Pydantic v2 base (unchanged core). Gains class attribute `USER_PARAM_REQUIRED: ClassVar[bool] = False`. When `True`, `list()`/`get()` auto-inject `user=<cached_user_id>` as query param.
3. **Mixin layer** (new) — one mixin per Reclaim trait. Resources compose the mixins they need. Each mixin declares `_PLANNER_PATH_SEGMENT: ClassVar[str]` (e.g. `"task"`, `"habit"`) so the same mixin wires the correct planner URL for each resource.

### Mixin inventory

| Mixin | Methods | Endpoints |
|---|---|---|
| `SnoozeableMixin` | `snooze(option, relative_from=None)`, `clear_snooze()` | `POST /api/planner/task/{id}/snooze`, `POST /api/planner/task/{id}/clear-snooze` |
| `StartStoppableMixin` | `start()`, `stop()` | `POST /api/planner/start/{segment}/{id}`, `POST /api/planner/stop/{segment}/{id}` |
| `RestartableMixin` | `restart()` | `POST /api/planner/restart/{segment}/{id}` |
| `LogWorkableMixin` | `log_work(minutes, end=None)` | `POST /api/planner/log-work/task/{id}` |
| `CompletableMixin` | `mark_complete()`, `mark_incomplete()` | `POST /api/planner/done/{segment}/{id}`, `POST /api/planner/unarchive/task/{id}` |
| `ClearExceptionsMixin` | `clear_exceptions()` | `POST /api/planner/clear-exceptions/{segment}/{id}` |
| `PlanWorkMixin` | `plan_work(dt, duration_minutes=None)` | `POST /api/planner/plan-work/task/{id}` |

### Resource composition

```
Task(BaseResource,
     SnoozeableMixin, StartStoppableMixin, RestartableMixin,
     LogWorkableMixin, CompletableMixin, ClearExceptionsMixin, PlanWorkMixin)

DailyHabit(BaseResource,
           StartStoppableMixin, RestartableMixin, ClearExceptionsMixin)

Hours(BaseResource)                 # unchanged
Webhook(BaseResource)               # new, CRUD only
```

### Non-resource modules

- `reclaim_sdk.webhooks.payloads` — `TaskWebhookEvent`, `HabitWebhookEvent`, `SchedulingLinkWebhookEvent` (discriminated union on `type`). `parse_webhook_payload(raw) → WebhookEvent`.
- `reclaim_sdk.webhooks.signature` — `verify_signature(body, header, secret) → bool` + `SignatureVerificationError`. Discovery step in implementation: register a test webhook in live mode, inspect incoming request headers. If a signature header exists (likely `X-Reclaim-Signature`), implement HMAC-SHA256 compare. If no signature header is emitted by Reclaim, ship the module with `verify_signature` raising `NotImplementedError("Reclaim does not currently sign webhook payloads")` and document the finding in the module docstring — consumers then know not to rely on it.
- `reclaim_sdk.resources.changelog` — `Changelog` namespace class (not `BaseResource`). Static methods wrap `GET /api/changelog/{tasks,events,scheduling-links,smart-habits,smart-meetings}`. Returns `list[ChangeLogEntryView]`.
- `reclaim_sdk.enums` — shared enums: `PriorityLevel`, `EventCategory`, `EventColor`, `TaskStatus`, `TaskSource`, `SnoozeOption`, `EventSubType`. `TaskPriority` is **removed** (breaking).

### Directory layout

```
reclaim_sdk/
  __init__.py              # __version__ = "0.7.0"
  client.py                # + current_user() cache
  exceptions.py            # + SignatureVerificationError
  enums.py                 # new
  mixins/
    __init__.py
    snoozeable.py
    start_stoppable.py
    restartable.py
    log_workable.py
    completable.py
    clear_exceptions.py
    plan_work.py
  resources/
    __init__.py
    base.py                # + USER_PARAM_REQUIRED, user auto-injection
    task.py                # updated schema + new endpoints
    hours.py               # unchanged
    habit.py               # new
    webhook.py             # new
    changelog.py           # new
  webhooks/
    __init__.py
    payloads.py
    signature.py
tests/
  conftest.py
  unit/
    test_client.py
    test_base_resource.py
    mixins/
    resources/
    webhooks/
    test_enums.py
  live/
    conftest.py            # cleanup fixtures, SDK_LIVE_PREFIX
    test_task_live.py
    test_habit_live.py
    test_webhook_live.py
    test_hours_live.py
    test_changelog_live.py
docs/superpowers/specs/
  2026-04-21-reclaim-api-parity-design.md
examples/
  task_management.py       # updated
  habit_management.py      # new
  webhooks.py              # new
  changelog.py             # new
```

## Components — per-resource detail

### `Task` (updated)

**Schema alignment with Swagger `Task`:**
- Required fields added: `taskSource` (enum `TaskSource`), `readOnlyFields` (`list[str]`), `sortKey` (`float`), `prioritizableType` (`str`), `type` (literal `"TASK"`).
- `eventSubType`: `Optional[str]` → `Optional[EventSubType]` (enum).
- `priority`: uses `PriorityLevel` (not local `TaskPriority`).
- `status`: reuse existing `TaskStatus`; verify enum values against Swagger (ensure `ARCHIVED` still valid).

**Properties (unchanged):** `duration`, `min_work_duration`, `max_work_duration`, `up_next`.

**Classmethods:**
- `Task.list(user=None, status=None, project=None, priority=None, id=None) → list[Task]` — auto-inject `user`.
- `Task.get(id, user=None) → Task` — auto-inject `user`.
- `Task.create_at_time(task: Task, start_time: datetime) → Task`  (new, `POST /api/tasks/at-time`)
- `Task.find_min_index(user=None) → float | None`  (new, `GET /api/tasks/min-index`)
- `Task.batch_patch(patches: list[TaskPatch]) → dict`  (new, `PATCH /api/tasks/batch`)
- `Task.batch_delete(patches: list[TaskPatch]) → dict`  (new, `DELETE /api/tasks/batch`)
- `Task.batch_archive(patches: list[TaskPatch]) → dict`  (new, `PATCH /api/tasks/batch/archive`)
- `Task.reindex_by_due() → list[Task]`  **(bug fix: use `ReclaimClient()` instead of broken `cls._client`)**
- `Task.register_interest(user: User) → None`  (new, `POST /api/tasks/interest`)

**Instance methods (beyond mixins):**
- `task.reindex(sort_key: float) → Task`  (new, `PATCH /api/tasks/{id}/reindex`)
- `task.reschedule_event(event_id: str) → Task`  (new, `POST /api/planner/reschedule/task/event/{eventId}`)
- `task.delete_policy() → None`  (new, `DELETE /api/planner/policy/task/{id}`)
- `task.save(strategy='patch') → None` — adds optional `strategy='put'` for full `PUT /api/tasks/{taskId}`

**`TaskPatch` model (new):**
```python
class TaskPatch(BaseModel):
    task_id: int = Field(alias="taskId")
    patch: dict[str, Any]
    notification_key: str | None = Field(None, alias="notificationKey")
```

### `DailyHabit` (new)

Full schema from Swagger `DailyHabit`. CRUD via `BaseResource`.

**Mixin-provided:** `start`, `stop`, `restart`, `clear_exceptions`.

**Habit-specific:**
- `habit.toggle(enable: bool | None = None)` → `POST /api/planner/toggle/habit/{id}`
- `habit.reschedule_event(event_id)` → `POST /api/planner/reschedule/habit/event/{eventId}`
- `habit.skip_event(event_id)` → `POST /api/planner/skip/habit/event/{eventId}`
- `habit.migrate_to_smart_series()` → `POST /api/assist/habits/daily/{id}/migrate-to-smart-series`
- `habit.delete_policy()` → `DELETE /api/planner/policy/habit/{id}`
- `DailyHabit.get_template(id)` / `DailyHabit.list_templates(role=None, department=None)` — `/api/assist/habits/template{,s}`
- `DailyHabit.create_from_template(template_id)` — deprecated by upstream, wrapped with `warnings.warn(DeprecationWarning)`.

### `Webhook` (new)

Endpoint: `/api/team/current/webhooks`. Standard CRUD via `BaseResource`.

**Fields** (from Swagger `Webhook` schema — confirmed during impl): `id`, `url`, `events` (`list[str]`), `secret` (optional), `created`, `updated`.

### Payload models (`reclaim_sdk.webhooks.payloads`)

```python
class WebhookEventBase(BaseModel):
    event_id: str
    type: Literal[...]   # discriminator
    created: datetime

class TaskWebhookEvent(WebhookEventBase):
    type: Literal["task.created", "task.updated", "task.completed", "task.deleted"]
    task: Task

class HabitWebhookEvent(WebhookEventBase):
    type: Literal["habit.created", "habit.updated", "habit.deleted"]
    habit: DailyHabit

# discriminated union
WebhookEvent = Annotated[
    TaskWebhookEvent | HabitWebhookEvent | ...,
    Field(discriminator="type"),
]

def parse_webhook_payload(raw: bytes | str) -> WebhookEvent: ...
```

Exact `type` literals confirmed during implementation by subscribing a test webhook and observing payload shapes (live mode).

### `Changelog` (new)

Namespace-style class — no lifecycle.

```python
class Changelog:
    @staticmethod
    def tasks(task_ids: list[int], client=None) -> list[ChangeLogEntryView]: ...
    @staticmethod
    def events(event_ids: list[str], client=None) -> list[ChangeLogEntryView]: ...
    @staticmethod
    def smart_habits(ids: list[int], client=None) -> list[ChangeLogEntryView]: ...
    @staticmethod
    def smart_meetings(ids: list[int], client=None) -> list[ChangeLogEntryView]: ...
    @staticmethod
    def scheduling_links(ids: list[str], client=None) -> list[ChangeLogEntryView]: ...
    @staticmethod
    def all(client=None) -> list[ChangeLogEntryView]: ...
```

## Data flow

### User-param auto-injection

1. User calls `Task.list()`.
2. `BaseResource.list()` sees `cls.USER_PARAM_REQUIRED=True` → calls `client.current_user()`.
3. `current_user()`: if cache set, return cached; else `GET /api/users/current`, parse `User`, cache.
4. `params["user"]` injected (serialized per Swagger — exact shape validated during TDD).
5. Request goes out, response parsed, list returned.

### Planner action (mixin example)

```python
class SnoozeableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"  # overridden per resource

    def snooze(self, option: SnoozeOption | None = None,
               relative_from: datetime | None = None) -> None:
        params: dict = {}
        if option: params["snoozeOption"] = option.value
        if relative_from: params["relativeFrom"] = relative_from.isoformat()
        response = self._client.post(
            f"/api/planner/{self._PLANNER_PATH_SEGMENT}/{self.id}/snooze",
            params=params,
        )
        # response is PlannerActionIntermediateResult, task payload under taskOrHabit
        data = response.get("taskOrHabit", response)
        self.__dict__.update(self.from_api_data(data).__dict__)
```

### Webhook ingestion

Consumer code (outside SDK):
```python
from reclaim_sdk.webhooks import parse_webhook_payload, verify_signature

@app.post("/reclaim-hook")
def hook(request):
    verify_signature(request.body, request.headers["X-Reclaim-Signature"], SECRET)
    event = parse_webhook_payload(request.body)
    match event:
        case TaskWebhookEvent():
            handle_task(event.task)
```

## Error handling

- `ReclaimClient.request()` status → exception mapping unchanged.
- `SignatureVerificationError(ReclaimAPIError)` raised when HMAC compare fails.
- `parse_webhook_payload` raises Pydantic's `ValidationError` on unknown event type (no silent-drop — caller decides).
- Live-mode teardown failures surface as pytest session errors (not swallowed).

## Testing

### Mocked unit tests (default)

- Framework: `pytest` + `respx`.
- Each endpoint gets a test verifying exact URL, method, query params, request body, and response parsing.
- Mixin tests parameterized across resources (`_PLANNER_PATH_SEGMENT` values) so one test suite covers Task + Habit variants.
- `ReclaimClient.current_user()` tested for caching behavior (called once across multiple `Task.list()` calls).

### Live tests (`RECLAIM_LIVE_TEST=1`)

- `pytest -m live` runs suite against real API.
- Session-scoped prefix: `SDK_LIVE_PREFIX = f"[sdk-test-{uuid4().hex[:8]}]"`. Every created entity's `title` starts with this prefix.
- Session-scoped `tracked_ids` fixture collects created ids per resource type.
- Session finalizer: delete every tracked id. Any delete that fails → session error (not swallowed).
- Paranoid sweep after finalizer: `Task.list()`, `DailyHabit.list()`, `Webhook.list()` — delete any entity whose title still starts with `SDK_LIVE_PREFIX`.
- CI does **not** run live tests (no secret exposed). Contributors opt in locally.

### TDD cadence (vertical slice)

Each endpoint = one red/green/refactor cycle:
1. Write failing respx-mocked unit test.
2. Implement minimum code to pass.
3. Refactor (extract mixin if duplication emerges).
4. Add matching live test (skipped unless env flag set).
5. Commit.

Order defined in implementation plan (writing-plans skill, next step).

### Coverage

- Target ≥95% line coverage on new modules (`mixins/`, `resources/habit.py`, `resources/webhook.py`, `resources/changelog.py`, `webhooks/`, `enums.py`).
- Target ≥90% overall (`BaseResource` is already exercised).
- Enforced via `pytest --cov` in CI PR checks (add to workflow).

## Release checklist

- [ ] Bump `reclaim_sdk/__init__.py` → `__version__ = "0.7.0"`.
- [ ] `CHANGELOG.md` (new file) with **Breaking Changes** section (TaskPriority removed, user param auto-resolved, new required Task fields, planner action return value unwrapped).
- [ ] `README.md` migration notes (top of file).
- [ ] `examples/task_management.py` updated to use `PriorityLevel`.
- [ ] `examples/habit_management.py`, `examples/webhooks.py`, `examples/changelog.py` created.
- [ ] `setup.py` `extras_require["dev"]` adds `pytest`, `respx`, `pytest-cov`.
- [ ] `.github/workflows/` — new `ci.yml` runs lint + mocked tests on PR (publish workflow unchanged).
- [ ] PyPI publish triggers on merge to master (existing workflow).

## Out of scope

Not in this release: Events, Calendars, Scheduling Links, One-on-Ones, Analytics, Focus Settings, Integrations (Asana/ClickUp), API key management, Admin operations, Delegated Access, Account Time Schemes. Each becomes its own follow-up spec once 0.7.0 ships.
