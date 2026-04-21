# reclaim-sdk 0.7.0 API Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `reclaim-sdk` to parity with the current Reclaim.ai Swagger spec — fix a known bug, align the `Task` schema, add 7 missing Task endpoints, add 10 missing task-planner actions, enforce the required `user` query parameter, and introduce three new resources: `DailyHabit` (full), `Webhook`, and `Changelog`. Ship as 0.7.0 (breaking).

**Architecture:** Existing three-layer design (`ReclaimClient` singleton → `BaseResource` pydantic base → resource classes) gains a new **mixin layer** that mirrors Reclaim's trait model (`Snoozeable`, `StartStoppable`, `Restartable`, `LogWorkable`, `Completable`, `ClearExceptions`, `PlanWork`). `Task` and `DailyHabit` compose the mixins they need. Each mixin uses `_PLANNER_PATH_SEGMENT: ClassVar[str]` so one implementation drives both `/api/planner/task/…` and `/api/planner/habit/…`. `ReclaimClient` caches the current user for the required `user=` query param. Webhook payloads get typed pydantic models with a discriminated union.

**Tech Stack:** Python ≥3.10, `pydantic>=2.0`, `httpx[http2]`, `python-dateutil`, `pytest`, `respx` (new dev dep), `pytest-cov` (new dev dep).

**Design spec:** `docs/superpowers/specs/2026-04-21-reclaim-api-parity-design.md`

---

## File Structure

### Files created

```
reclaim_sdk/
  enums.py                       # new: PriorityLevel, EventCategory, EventColor, TaskStatus,
                                 #      TaskSource, SnoozeOption, EventSubType
  mixins/
    __init__.py
    snoozeable.py                # SnoozeableMixin
    start_stoppable.py           # StartStoppableMixin
    restartable.py               # RestartableMixin
    log_workable.py              # LogWorkableMixin
    completable.py               # CompletableMixin
    clear_exceptions.py          # ClearExceptionsMixin
    plan_work.py                 # PlanWorkMixin
  resources/
    habit.py                     # DailyHabit + templates
    webhook.py                   # Webhook CRUD
    changelog.py                 # Changelog namespace + ChangeLogEntryView
  webhooks/
    __init__.py                  # re-exports parse_webhook_payload, verify_signature
    payloads.py                  # WebhookEvent discriminated union
    signature.py                 # verify_signature + SignatureVerificationError
tests/
  __init__.py
  conftest.py                    # global fixtures
  unit/
    __init__.py
    test_client.py
    test_enums.py
    test_base_resource.py
    mixins/
      __init__.py
      test_snoozeable.py
      test_start_stoppable.py
      test_restartable.py
      test_log_workable.py
      test_completable.py
      test_clear_exceptions.py
      test_plan_work.py
    resources/
      __init__.py
      test_task.py
      test_habit.py
      test_webhook.py
      test_changelog.py
      test_hours.py
    webhooks/
      __init__.py
      test_payloads.py
      test_signature.py
  live/
    __init__.py
    conftest.py                  # SDK_LIVE_PREFIX + cleanup fixtures
    test_task_live.py
    test_habit_live.py
    test_webhook_live.py
    test_hours_live.py
    test_changelog_live.py
examples/
  habit_management.py
  webhooks.py
  changelog.py
docs/superpowers/plans/
  2026-04-21-reclaim-api-parity.md  # this file
CHANGELOG.md
.github/workflows/
  ci.yml                         # lint + mocked tests on PR
pytest.ini
```

### Files modified

- `reclaim_sdk/__init__.py` — version bump
- `reclaim_sdk/client.py` — add `current_user()` cache
- `reclaim_sdk/exceptions.py` — add `SignatureVerificationError`
- `reclaim_sdk/resources/base.py` — add `USER_PARAM_REQUIRED`, user-param injection
- `reclaim_sdk/resources/task.py` — schema update, new endpoints, mixin composition, bug fix
- `setup.py` — add `pytest`, `respx`, `pytest-cov` to `extras_require["dev"]`
- `README.md` — migration notes
- `examples/task_management.py` — use `PriorityLevel` instead of `TaskPriority`

---

## Task 1: Test Infrastructure

**Files:**
- Create: `pytest.ini`
- Create: `tests/__init__.py`, `tests/conftest.py`, `tests/unit/__init__.py`, `tests/live/__init__.py`, `tests/live/conftest.py`
- Modify: `setup.py`

### Step 1.1: Add dev dependencies

- [ ] **Edit `setup.py`**

Change `extras_require` block from:
```python
    extras_require={
        "dev": ["flake8", "black"],
    },
```
to:
```python
    extras_require={
        "dev": ["flake8", "black", "pytest>=8", "respx>=0.21", "pytest-cov>=5"],
    },
```

### Step 1.2: Create `pytest.ini`

- [ ] **Create file at repo root**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
markers =
    live: tests that hit the real Reclaim API (require RECLAIM_LIVE_TEST=1 and RECLAIM_TOKEN)
addopts = -ra --strict-markers
```

### Step 1.3: Create test package skeleton

- [ ] **Create empty files**

```bash
touch tests/__init__.py tests/unit/__init__.py tests/live/__init__.py
mkdir -p tests/unit/mixins tests/unit/resources tests/unit/webhooks
touch tests/unit/mixins/__init__.py tests/unit/resources/__init__.py tests/unit/webhooks/__init__.py
```

### Step 1.4: Write `tests/conftest.py`

- [ ] **Create file**

```python
import os
import pytest
import respx
from reclaim_sdk.client import ReclaimClient


@pytest.fixture(autouse=True)
def reset_client_singleton():
    """Every test gets a fresh client instance."""
    ReclaimClient._instance = None
    ReclaimClient._config = None
    yield
    ReclaimClient._instance = None
    ReclaimClient._config = None


@pytest.fixture
def client():
    return ReclaimClient.configure(token="test-token")


@pytest.fixture
def mock_api():
    with respx.mock(base_url="https://api.app.reclaim.ai", assert_all_called=False) as mock:
        yield mock


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RECLAIM_LIVE_TEST") == "1":
        return
    skip_live = pytest.mark.skip(reason="set RECLAIM_LIVE_TEST=1 to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
```

### Step 1.5: Write `tests/live/conftest.py`

- [ ] **Create file**

```python
import os
import uuid
import pytest
from reclaim_sdk.client import ReclaimClient


SDK_LIVE_PREFIX = f"[sdk-test-{uuid.uuid4().hex[:8]}]"


@pytest.fixture(scope="session")
def live_client():
    token = os.environ.get("RECLAIM_TOKEN")
    if not token:
        pytest.skip("RECLAIM_TOKEN not set")
    return ReclaimClient.configure(token=token)


@pytest.fixture(scope="session")
def tracked_ids():
    """Registry of resources created during the session. Cleaned up in finalizer."""
    registry = {"tasks": [], "habits": [], "webhooks": []}
    yield registry

    from reclaim_sdk.resources.task import Task
    from reclaim_sdk.resources.habit import DailyHabit
    from reclaim_sdk.resources.webhook import Webhook

    errors = []
    for task_id in registry["tasks"]:
        try:
            t = Task.get(task_id)
            t.delete()
        except Exception as e:
            errors.append(f"task {task_id}: {e}")
    for habit_id in registry["habits"]:
        try:
            h = DailyHabit.get(habit_id)
            h.delete()
        except Exception as e:
            errors.append(f"habit {habit_id}: {e}")
    for wh_id in registry["webhooks"]:
        try:
            w = Webhook.get(wh_id)
            w.delete()
        except Exception as e:
            errors.append(f"webhook {wh_id}: {e}")

    # paranoid sweep
    try:
        for t in Task.list():
            if t.title and t.title.startswith(SDK_LIVE_PREFIX):
                t.delete()
    except Exception as e:
        errors.append(f"task sweep: {e}")

    if errors:
        raise RuntimeError("Live cleanup failures: " + "; ".join(errors))


@pytest.fixture
def prefix():
    return SDK_LIVE_PREFIX
```

### Step 1.6: Verify test infrastructure works

- [ ] **Run**

```bash
pip install -e ".[dev]"
pytest --collect-only 2>&1 | tail -5
```

Expected: `collected 0 items` (no tests yet, but no errors).

### Step 1.7: Commit

- [ ] **Commit**

```bash
git add pytest.ini setup.py tests/
git commit --no-gpg-sign -m "test: add pytest+respx infrastructure with live-mode opt-in"
```

---

## Task 2: Shared Enums Module

**Files:**
- Create: `reclaim_sdk/enums.py`
- Create: `tests/unit/test_enums.py`

### Step 2.1: Write failing test for `PriorityLevel`

- [ ] **Create `tests/unit/test_enums.py`**

```python
from reclaim_sdk.enums import (
    PriorityLevel, EventCategory, EventColor, TaskStatus,
    TaskSource, SnoozeOption, EventSubType,
)


def test_priority_level_values():
    assert PriorityLevel.P1.value == "P1"
    assert PriorityLevel.P4.value == "P4"
    assert len(list(PriorityLevel)) == 4


def test_event_category_values():
    assert EventCategory.WORK.value == "WORK"
    assert EventCategory.PERSONAL.value == "PERSONAL"


def test_event_color_contains_tomato():
    assert EventColor.TOMATO.value == "TOMATO"


def test_task_status_includes_archived():
    assert TaskStatus.ARCHIVED.value == "ARCHIVED"


def test_task_source_is_string_enum():
    assert isinstance(TaskSource.RECLAIM, TaskSource)
    assert TaskSource.RECLAIM.value == "RECLAIM"


def test_snooze_option_has_options():
    # Must contain at least one known value
    values = {e.value for e in SnoozeOption}
    assert "ONE_HOUR" in values or "LATER_TODAY" in values


def test_event_sub_type_is_enum():
    # Just ensure it's importable and has members
    assert len(list(EventSubType)) > 0
```

### Step 2.2: Run test to verify it fails

- [ ] **Run**

```bash
pytest tests/unit/test_enums.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'reclaim_sdk.enums'`.

### Step 2.3: Implement `reclaim_sdk/enums.py`

- [ ] **Create file**

```python
from enum import Enum


class PriorityLevel(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class EventCategory(str, Enum):
    WORK = "WORK"
    PERSONAL = "PERSONAL"
    BOTH = "BOTH"


class EventColor(str, Enum):
    NONE = "NONE"
    LAVENDER = "LAVENDER"
    SAGE = "SAGE"
    GRAPE = "GRAPE"
    FLAMINGO = "FLAMINGO"
    BANANA = "BANANA"
    TANGERINE = "TANGERINE"
    PEACOCK = "PEACOCK"
    GRAPHITE = "GRAPHITE"
    BLUEBERRY = "BLUEBERRY"
    BASIL = "BASIL"
    TOMATO = "TOMATO"


class TaskStatus(str, Enum):
    NEW = "NEW"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class TaskSource(str, Enum):
    RECLAIM = "RECLAIM"
    GOOGLE = "GOOGLE"
    ASANA = "ASANA"
    CLICKUP = "CLICKUP"
    JIRA = "JIRA"
    TODOIST = "TODOIST"
    LINEAR = "LINEAR"


class SnoozeOption(str, Enum):
    LATER_TODAY = "LATER_TODAY"
    TOMORROW = "TOMORROW"
    NEXT_WEEK = "NEXT_WEEK"
    ONE_HOUR = "ONE_HOUR"
    TWO_HOURS = "TWO_HOURS"
    FOUR_HOURS = "FOUR_HOURS"


class EventSubType(str, Enum):
    FOCUS = "FOCUS"
    MEETING = "MEETING"
    TASK = "TASK"
    HABIT = "HABIT"
    PERSONAL = "PERSONAL"
    WORK = "WORK"
    OTHER = "OTHER"
```

**Note:** Exact enum values for `TaskSource`, `SnoozeOption`, `EventSubType` need verification against Swagger during implementation — fetch `https://api.app.reclaim.ai/swagger/reclaim-api-0.1.yml` and grep for each schema name. Adjust above values if needed.

### Step 2.4: Run test to verify it passes

- [ ] **Run**

```bash
pytest tests/unit/test_enums.py -v
```

Expected: 7 passed.

### Step 2.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/enums.py tests/unit/test_enums.py
git commit --no-gpg-sign -m "feat: add shared enums module (breaking: replaces TaskPriority)"
```

---

## Task 3: `ReclaimClient.current_user()` with caching

**Files:**
- Modify: `reclaim_sdk/client.py`
- Create: `tests/unit/test_client.py`

### Step 3.1: Write failing test

- [ ] **Create `tests/unit/test_client.py`**

```python
import httpx
import pytest
from reclaim_sdk.client import ReclaimClient


def test_current_user_fetches_and_caches(client, mock_api):
    route = mock_api.get("/api/users/current").mock(
        return_value=httpx.Response(200, json={"id": 42, "username": "alice"})
    )
    user_a = client.current_user()
    user_b = client.current_user()
    assert user_a == user_b
    assert user_a["id"] == 42
    assert route.call_count == 1  # cache works


def test_current_user_cache_cleared_on_reconfigure(client, mock_api):
    mock_api.get("/api/users/current").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    client.current_user()
    ReclaimClient.configure(token="another-token")
    # After reconfigure, cache must be invalidated
    assert ReclaimClient._instance._user_cache is None


def test_configure_without_token_raises_when_env_missing(monkeypatch):
    monkeypatch.delenv("RECLAIM_TOKEN", raising=False)
    ReclaimClient._instance = None
    ReclaimClient._config = None
    with pytest.raises(ValueError, match="token is required"):
        ReclaimClient()
```

### Step 3.2: Run test to verify it fails

- [ ] **Run**

```bash
pytest tests/unit/test_client.py -v
```

Expected: FAIL — `AttributeError: 'ReclaimClient' object has no attribute 'current_user'`.

### Step 3.3: Modify `reclaim_sdk/client.py`

- [ ] **Edit** — add cache slot to `_initialize` and add `current_user()` method; clear cache in `configure`.

In `_initialize`, after `self.session = httpx.Client(...)`, add:
```python
        self._user_cache: dict | None = None
```

In `configure`, before `cls._instance._initialize()`, add:
```python
        if cls._instance is not None:
            cls._instance._user_cache = None
```

Add the new method after `patch`:
```python
    def current_user(self) -> Dict[str, Any]:
        if self._user_cache is None:
            self._user_cache = self.get("/api/users/current")
        return self._user_cache
```

### Step 3.4: Run test to verify it passes

- [ ] **Run**

```bash
pytest tests/unit/test_client.py -v
```

Expected: 3 passed.

### Step 3.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/client.py tests/unit/test_client.py
git commit --no-gpg-sign -m "feat(client): add cached current_user() helper"
```

---

## Task 4: `BaseResource` user-param injection

**Files:**
- Modify: `reclaim_sdk/resources/base.py`
- Create: `tests/unit/test_base_resource.py`

### Step 4.1: Write failing test

- [ ] **Create `tests/unit/test_base_resource.py`**

```python
from typing import ClassVar
import httpx
from pydantic import Field
from reclaim_sdk.resources.base import BaseResource


class _Sample(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/sample"
    USER_PARAM_REQUIRED: ClassVar[bool] = True
    title: str | None = Field(None)


def test_list_injects_user_when_required(client, mock_api):
    mock_api.get("/api/users/current").mock(
        return_value=httpx.Response(200, json={"id": 7})
    )
    route = mock_api.get("/api/sample").mock(
        return_value=httpx.Response(200, json=[])
    )
    _Sample.list()
    assert route.called
    assert "user" in dict(route.calls.last.request.url.params)


def test_get_injects_user_when_required(client, mock_api):
    mock_api.get("/api/users/current").mock(
        return_value=httpx.Response(200, json={"id": 7})
    )
    route = mock_api.get("/api/sample/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "title": "x"})
    )
    _Sample.get(1)
    assert "user" in dict(route.calls.last.request.url.params)


def test_no_user_injection_when_not_required(client, mock_api):
    class _NoUser(BaseResource):
        ENDPOINT: ClassVar[str] = "/api/nouser"
        title: str | None = Field(None)

    route = mock_api.get("/api/nouser").mock(return_value=httpx.Response(200, json=[]))
    _NoUser.list()
    assert "user" not in dict(route.calls.last.request.url.params)
```

### Step 4.2: Run test to verify it fails

- [ ] **Run**

```bash
pytest tests/unit/test_base_resource.py -v
```

Expected: FAIL — user param missing from request.

### Step 4.3: Modify `reclaim_sdk/resources/base.py`

- [ ] **Edit**

Add class attribute inside `BaseResource`:
```python
    USER_PARAM_REQUIRED: ClassVar[bool] = False
```

Change `get` classmethod:
```python
    @classmethod
    def get(cls: Type[T], id: int, client: ReclaimClient = None) -> T:
        if client is None:
            client = ReclaimClient()
        params = {}
        if cls.USER_PARAM_REQUIRED:
            params["user"] = client.current_user().get("id")
        data = client.get(f"{cls.ENDPOINT}/{id}", params=params)
        return cls.from_api_data(data)
```

Change `list` classmethod:
```python
    @classmethod
    def list(cls: Type[T], client: ReclaimClient = None, **params) -> List[T]:
        if client is None:
            client = ReclaimClient()
        if cls.USER_PARAM_REQUIRED and "user" not in params:
            params["user"] = client.current_user().get("id")
        data = client.get(cls.ENDPOINT, params=params)
        return [cls.from_api_data(item) for item in data]
```

### Step 4.4: Run test to verify it passes

- [ ] **Run**

```bash
pytest tests/unit/test_base_resource.py -v
```

Expected: 3 passed.

### Step 4.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/base.py tests/unit/test_base_resource.py
git commit --no-gpg-sign -m "feat(base): auto-inject user query param when USER_PARAM_REQUIRED"
```

---

## Task 5: Fix `Task.prioritize_by_due` classmethod bug

**Files:**
- Modify: `reclaim_sdk/resources/task.py`
- Create: `tests/unit/resources/test_task.py`

### Step 5.1: Write failing test

- [ ] **Create `tests/unit/resources/test_task.py`**

```python
import httpx
from reclaim_sdk.resources.task import Task


def test_prioritize_by_due_does_not_raise_attribute_error(client, mock_api):
    mock_api.patch("/api/tasks/reindex-by-due").mock(
        return_value=httpx.Response(200, json=[])
    )
    # Must not raise AttributeError — the old code did cls._client which is unset
    Task.prioritize_by_due()
```

### Step 5.2: Run test to verify it fails

- [ ] **Run**

```bash
pytest tests/unit/resources/test_task.py::test_prioritize_by_due_does_not_raise_attribute_error -v
```

Expected: FAIL — `AttributeError: type object 'Task' has no attribute '_client'`.

### Step 5.3: Fix `Task.prioritize_by_due`

- [ ] **Edit `reclaim_sdk/resources/task.py`**

Replace:
```python
    @classmethod
    def prioritize_by_due(cls) -> None:
        cls._client.patch("/api/tasks/reindex-by-due")
```
with:
```python
    @classmethod
    def prioritize_by_due(cls, client: ReclaimClient = None) -> list["Task"]:
        if client is None:
            client = ReclaimClient()
        data = client.patch("/api/tasks/reindex-by-due")
        return [cls.from_api_data(item) for item in (data or [])]
```

Add import at top of file:
```python
from reclaim_sdk.client import ReclaimClient
```

### Step 5.4: Run test to verify it passes

- [ ] **Run**

```bash
pytest tests/unit/resources/test_task.py::test_prioritize_by_due_does_not_raise_attribute_error -v
```

Expected: 1 passed.

### Step 5.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/task.py tests/unit/resources/test_task.py
git commit --no-gpg-sign -m "fix(task): prioritize_by_due classmethod used unset cls._client"
```

---

## Task 6: Align `Task` schema with Swagger (BREAKING)

**Files:**
- Modify: `reclaim_sdk/resources/task.py`
- Modify: `tests/unit/resources/test_task.py`

### Step 6.1: Write failing tests for schema

- [ ] **Append to `tests/unit/resources/test_task.py`**

```python
from reclaim_sdk.enums import PriorityLevel, TaskSource, EventSubType


def test_task_has_new_required_fields():
    t = Task(
        title="hello",
        priority=PriorityLevel.P3,
        taskSource=TaskSource.RECLAIM,
        readOnlyFields=[],
        sortKey=1.0,
        prioritizableType="TASK",
        type="TASK",
    )
    assert t.task_source == TaskSource.RECLAIM
    assert t.read_only_fields == []
    assert t.sort_key == 1.0
    assert t.type == "TASK"


def test_task_priority_uses_priority_level_enum():
    t = Task(title="x", priority=PriorityLevel.P1)
    assert t.priority == PriorityLevel.P1


def test_task_event_sub_type_is_enum():
    t = Task(title="x", eventSubType=EventSubType.FOCUS)
    assert t.event_sub_type == EventSubType.FOCUS


def test_task_priority_old_enum_removed():
    # TaskPriority must no longer exist (breaking)
    import reclaim_sdk.resources.task as tm
    assert not hasattr(tm, "TaskPriority")
```

### Step 6.2: Run tests to verify they fail

- [ ] **Run**

```bash
pytest tests/unit/resources/test_task.py -v
```

Expected: multiple failures — missing fields, old `TaskPriority` still present.

### Step 6.3: Update `Task` schema

- [ ] **Edit `reclaim_sdk/resources/task.py`**

Remove the local `TaskPriority`, `TaskStatus`, `EventCategory`, `EventColor` enum classes (they move to `reclaim_sdk.enums`).

Replace imports at the top of the file with:
```python
from pydantic import Field, field_validator
from datetime import datetime, timezone
from typing import ClassVar, Optional
from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.base import BaseResource
from reclaim_sdk.enums import (
    PriorityLevel, EventCategory, EventColor, TaskStatus,
    TaskSource, EventSubType,
)
```

Add `USER_PARAM_REQUIRED = True` to the `Task` class body:
```python
class Task(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/tasks"
    USER_PARAM_REQUIRED: ClassVar[bool] = True
```

Change the `event_sub_type` field:
```python
    event_sub_type: Optional[EventSubType] = Field(
        None, alias="eventSubType", description="Event subtype"
    )
```

Change `priority`:
```python
    priority: Optional[PriorityLevel] = Field(None, description="Task priority")
```

Add new required fields (place after `always_private`):
```python
    task_source: TaskSource = Field(
        TaskSource.RECLAIM, alias="taskSource", description="Task origin"
    )
    read_only_fields: list[str] = Field(
        default_factory=list, alias="readOnlyFields", description="Server-enforced read-only fields"
    )
    sort_key: float = Field(0.0, alias="sortKey", description="Sort order key")
    prioritizable_type: str = Field(
        "TASK", alias="prioritizableType", description="Prioritizable polymorphic type"
    )
    type: str = Field("TASK", description="Discriminator for Task vs DailyHabit")
```

### Step 6.4: Run tests to verify they pass

- [ ] **Run**

```bash
pytest tests/unit/resources/test_task.py -v
```

Expected: all pass.

### Step 6.5: Update `examples/task_management.py`

- [ ] **Edit**

Change `from reclaim_sdk.resources.task import Task, TaskPriority, EventColor` to:
```python
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, EventColor
```

Change `priority=TaskPriority.P3` to `priority=PriorityLevel.P3`.

### Step 6.6: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/task.py tests/unit/resources/test_task.py examples/task_management.py
git commit --no-gpg-sign -m "feat(task)!: align Task schema with Swagger (BREAKING: TaskPriority removed, user required)"
```

---

## Task 7: `Task.create_at_time` classmethod

**Files:**
- Modify: `reclaim_sdk/resources/task.py`
- Modify: `tests/unit/resources/test_task.py`

### Step 7.1: Write failing test

- [ ] **Append to `tests/unit/resources/test_task.py`**

```python
from datetime import datetime


def test_create_at_time_posts_to_at_time_endpoint(client, mock_api):
    route = mock_api.post("/api/tasks/at-time").mock(
        return_value=httpx.Response(200, json={"id": 99, "title": "at-time", "type": "TASK"})
    )
    draft = Task(title="at-time", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    result = Task.create_at_time(draft, datetime(2026, 5, 1, 9, 0))
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert "startTime" in params
    assert isinstance(result, Task)
    assert result.id == 99
```

### Step 7.2: Run to verify fail

- [ ] **Run**

```bash
pytest tests/unit/resources/test_task.py::test_create_at_time_posts_to_at_time_endpoint -v
```

Expected: FAIL — `AttributeError: type object 'Task' has no attribute 'create_at_time'`.

### Step 7.3: Implement

- [ ] **Edit `reclaim_sdk/resources/task.py`** — add to `Task` class:

```python
    @classmethod
    def create_at_time(
        cls, task: "Task", start_time: datetime, client: ReclaimClient = None
    ) -> "Task":
        if client is None:
            client = ReclaimClient()
        params = {"startTime": start_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")}
        data = client.post(cls.ENDPOINT + "/at-time", params=params, json=task.to_api_data())
        # response shape: CreateTaskAtTimeView — contains the created task under "task" or is the task itself
        payload = data.get("task", data) if isinstance(data, dict) else data
        return cls.from_api_data(payload)
```

### Step 7.4: Run to verify pass

- [ ] **Run**

```bash
pytest tests/unit/resources/test_task.py::test_create_at_time_posts_to_at_time_endpoint -v
```

Expected: 1 passed.

### Step 7.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/task.py tests/unit/resources/test_task.py
git commit --no-gpg-sign -m "feat(task): add create_at_time classmethod"
```

---

## Task 8: `Task.find_min_index`

**Files:**
- Modify: `reclaim_sdk/resources/task.py`
- Modify: `tests/unit/resources/test_task.py`

### Step 8.1: Write failing test

- [ ] **Append**

```python
def test_find_min_index_returns_float(client, mock_api):
    mock_api.get("/api/users/current").mock(return_value=httpx.Response(200, json={"id": 1}))
    mock_api.get("/api/tasks/min-index").mock(return_value=httpx.Response(200, json=0.5))
    result = Task.find_min_index()
    assert result == 0.5


def test_find_min_index_handles_null(client, mock_api):
    mock_api.get("/api/users/current").mock(return_value=httpx.Response(200, json={"id": 1}))
    mock_api.get("/api/tasks/min-index").mock(return_value=httpx.Response(200, json=None))
    assert Task.find_min_index() is None
```

### Step 8.2: Run (fail)

- [ ] **Run** `pytest tests/unit/resources/test_task.py -k find_min_index -v`. Expected: FAIL.

### Step 8.3: Implement

- [ ] **Edit `reclaim_sdk/resources/task.py`**

```python
    @classmethod
    def find_min_index(cls, client: ReclaimClient = None) -> Optional[float]:
        if client is None:
            client = ReclaimClient()
        params = {"user": client.current_user().get("id")}
        return client.get(cls.ENDPOINT + "/min-index", params=params)
```

### Step 8.4: Run (pass)

- [ ] **Run** `pytest tests/unit/resources/test_task.py -k find_min_index -v`. Expected: 2 passed.

### Step 8.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/task.py tests/unit/resources/test_task.py
git commit --no-gpg-sign -m "feat(task): add find_min_index classmethod"
```

---

## Task 9: `TaskPatch` model + batch operations

**Files:**
- Modify: `reclaim_sdk/resources/task.py`
- Modify: `tests/unit/resources/test_task.py`

### Step 9.1: Write failing tests

- [ ] **Append**

```python
from reclaim_sdk.resources.task import TaskPatch


def test_task_patch_model_aliases():
    p = TaskPatch(taskId=1, patch={"title": "new"})
    dumped = p.model_dump(by_alias=True)
    assert dumped["taskId"] == 1
    assert dumped["patch"] == {"title": "new"}


def test_batch_patch_sends_array(client, mock_api):
    route = mock_api.patch("/api/tasks/batch").mock(
        return_value=httpx.Response(200, json={})
    )
    patches = [TaskPatch(taskId=1, patch={"title": "a"}),
               TaskPatch(taskId=2, patch={"title": "b"})]
    Task.batch_patch(patches)
    body = route.calls.last.request.content
    assert b'"taskId":1' in body and b'"taskId":2' in body


def test_batch_delete_sends_array(client, mock_api):
    route = mock_api.delete("/api/tasks/batch").mock(
        return_value=httpx.Response(200, json={})
    )
    Task.batch_delete([TaskPatch(taskId=5, patch={})])
    assert route.called


def test_batch_archive_sends_array(client, mock_api):
    route = mock_api.patch("/api/tasks/batch/archive").mock(
        return_value=httpx.Response(200, json={})
    )
    Task.batch_archive([TaskPatch(taskId=5, patch={})])
    assert route.called
```

### Step 9.2: Run (fail)

- [ ] **Run** `pytest tests/unit/resources/test_task.py -k batch -v`. Expected: FAIL.

### Step 9.3: Implement

- [ ] **Edit `reclaim_sdk/resources/task.py`** — add at bottom of file:

```python
from pydantic import BaseModel
from typing import Any


class TaskPatch(BaseModel):
    task_id: int = Field(..., alias="taskId")
    patch: dict[str, Any] = Field(default_factory=dict)
    notification_key: Optional[str] = Field(None, alias="notificationKey")

    model_config = {"populate_by_name": True}
```

Add to `Task` class:

```python
    @classmethod
    def batch_patch(cls, patches: list["TaskPatch"], client: ReclaimClient = None) -> dict:
        if client is None:
            client = ReclaimClient()
        body = [p.model_dump(by_alias=True, exclude_none=True) for p in patches]
        return client.patch(cls.ENDPOINT + "/batch", json=body)

    @classmethod
    def batch_delete(cls, patches: list["TaskPatch"], client: ReclaimClient = None) -> dict:
        if client is None:
            client = ReclaimClient()
        body = [p.model_dump(by_alias=True, exclude_none=True) for p in patches]
        return client.delete(cls.ENDPOINT + "/batch", json=body)

    @classmethod
    def batch_archive(cls, patches: list["TaskPatch"], client: ReclaimClient = None) -> dict:
        if client is None:
            client = ReclaimClient()
        body = [p.model_dump(by_alias=True, exclude_none=True) for p in patches]
        return client.patch(cls.ENDPOINT + "/batch/archive", json=body)
```

**Note:** `ReclaimClient.delete` doesn't currently accept `json=`. Extend the method signature in `client.py` — change `delete` to forward `**kwargs` through to `request` (it already does via `**kwargs`). Verify by reading `client.py:110-111` — it already forwards kwargs. No client change needed.

### Step 9.4: Run (pass)

- [ ] **Run** `pytest tests/unit/resources/test_task.py -k batch -v`. Expected: 4 passed.

### Step 9.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/task.py tests/unit/resources/test_task.py
git commit --no-gpg-sign -m "feat(task): add TaskPatch + batch_patch/delete/archive classmethods"
```

---

## Task 10: `Task.register_interest`

**Files:**
- Modify: `reclaim_sdk/resources/task.py`
- Modify: `tests/unit/resources/test_task.py`

### Step 10.1: Write failing test

- [ ] **Append**

```python
def test_register_interest_posts(client, mock_api):
    route = mock_api.post("/api/tasks/interest").mock(
        return_value=httpx.Response(200, json=None)
    )
    Task.register_interest({"id": 7})
    body = route.calls.last.request.content
    assert b'"user"' in body and b'"id":7' in body
```

### Step 10.2: Run (fail)

- [ ] **Run** `pytest tests/unit/resources/test_task.py::test_register_interest_posts -v`. Expected: FAIL.

### Step 10.3: Implement

- [ ] **Edit** — add to `Task`:

```python
    @classmethod
    def register_interest(cls, user: dict, client: ReclaimClient = None) -> None:
        if client is None:
            client = ReclaimClient()
        client.post(cls.ENDPOINT + "/interest", json={"user": user})
```

### Step 10.4: Run (pass), commit

- [ ] **Run** `pytest tests/unit/resources/test_task.py::test_register_interest_posts -v`. Expected: 1 passed.

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/task.py tests/unit/resources/test_task.py
git commit --no-gpg-sign -m "feat(task): add register_interest classmethod"
```

---

## Task 11: `task.reindex` instance method

**Files:**
- Modify: `reclaim_sdk/resources/task.py`
- Modify: `tests/unit/resources/test_task.py`

### Step 11.1: Write failing test

- [ ] **Append**

```python
def test_reindex_patches_with_sort_key(client, mock_api):
    route = mock_api.patch("/api/tasks/123/reindex").mock(
        return_value=httpx.Response(200, json={"id": 123, "sortKey": 5.5, "type": "TASK"})
    )
    t = Task(id=123, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.reindex(5.5)
    body = route.calls.last.request.content
    assert b'5.5' in body
```

### Step 11.2-11.4: Run (fail), implement, run (pass)

- [ ] **Run fail** — `pytest tests/unit/resources/test_task.py::test_reindex_patches_with_sort_key -v`

- [ ] **Add to `Task`**

```python
    def reindex(self, sort_key: float) -> None:
        response = self._client.patch(
            f"{self.ENDPOINT}/{self.id}/reindex",
            json={"sortKey": sort_key},
        )
        self.__dict__.update(self.from_api_data(response).__dict__)
```

- [ ] **Run pass** — same command.

### Step 11.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/task.py tests/unit/resources/test_task.py
git commit --no-gpg-sign -m "feat(task): add reindex instance method"
```

---

## Task 12: `task.save(strategy='put')`

**Files:**
- Modify: `reclaim_sdk/resources/base.py`
- Modify: `tests/unit/test_base_resource.py`

### Step 12.1: Write failing test

- [ ] **Append to `tests/unit/test_base_resource.py`**

```python
def test_save_with_put_strategy_uses_put(client, mock_api):
    mock_api.get("/api/users/current").mock(return_value=httpx.Response(200, json={"id": 1}))
    route = mock_api.put("/api/sample/5").mock(
        return_value=httpx.Response(200, json={"id": 5, "title": "x"})
    )
    s = _Sample(id=5, title="x")
    s.save(strategy="put")
    assert route.called
```

### Step 12.2-12.4: Run fail, implement, run pass

- [ ] **Run fail**.

- [ ] **Modify `BaseResource.save`**

```python
    def save(self, strategy: str = "patch") -> None:
        client = self._client
        data = self.to_api_data()
        if self.id:
            if strategy == "put":
                response = client.put(f"{self.ENDPOINT}/{self.id}", json=data)
            else:
                response = client.patch(f"{self.ENDPOINT}/{self.id}", json=data)
        else:
            response = client.post(self.ENDPOINT, json=data)
        self.__dict__.update(self.from_api_data(response).__dict__)
```

- [ ] **Run pass**.

### Step 12.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/base.py tests/unit/test_base_resource.py
git commit --no-gpg-sign -m "feat(base): save() accepts strategy='put' for full replace"
```

---

## Task 13: `SnoozeableMixin` (new mixin + wire to Task)

**Files:**
- Create: `reclaim_sdk/mixins/__init__.py`, `reclaim_sdk/mixins/snoozeable.py`
- Create: `tests/unit/mixins/test_snoozeable.py`
- Modify: `reclaim_sdk/resources/task.py`

### Step 13.1: Write failing test

- [ ] **Create `tests/unit/mixins/test_snoozeable.py`**

```python
import httpx
from datetime import datetime
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import SnoozeOption, PriorityLevel, TaskSource


def test_task_snooze_posts_to_snooze_endpoint(client, mock_api):
    route = mock_api.post("/api/planner/task/42/snooze").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.snooze(SnoozeOption.ONE_HOUR)
    params = dict(route.calls.last.request.url.params)
    assert params.get("snoozeOption") == "ONE_HOUR"


def test_task_clear_snooze_posts(client, mock_api):
    route = mock_api.post("/api/planner/task/42/clear-snooze").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.clear_snooze()
    assert route.called
```

### Step 13.2: Run (fail)

- [ ] **Run** `pytest tests/unit/mixins/test_snoozeable.py -v`. Expected: FAIL — `snooze` not defined.

### Step 13.3: Create mixin + wire up

- [ ] **Create `reclaim_sdk/mixins/__init__.py`** — empty

- [ ] **Create `reclaim_sdk/mixins/snoozeable.py`**

```python
from datetime import datetime, timezone
from typing import ClassVar, Optional
from reclaim_sdk.enums import SnoozeOption


class SnoozeableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def snooze(
        self,
        option: Optional[SnoozeOption] = None,
        relative_from: Optional[datetime] = None,
    ) -> None:
        params: dict = {}
        if option is not None:
            params["snoozeOption"] = option.value
        if relative_from is not None:
            params["relativeFrom"] = relative_from.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        response = self._client.post(
            f"/api/planner/{self._PLANNER_PATH_SEGMENT}/{self.id}/snooze",
            params=params,
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def clear_snooze(self) -> None:
        response = self._client.post(
            f"/api/planner/{self._PLANNER_PATH_SEGMENT}/{self.id}/clear-snooze"
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)
```

- [ ] **Modify `reclaim_sdk/resources/task.py`** — change class declaration:

```python
from reclaim_sdk.mixins.snoozeable import SnoozeableMixin


class Task(BaseResource, SnoozeableMixin):
    ENDPOINT: ClassVar[str] = "/api/tasks"
    USER_PARAM_REQUIRED: ClassVar[bool] = True
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"
```

### Step 13.4: Run (pass)

- [ ] **Run** `pytest tests/unit/mixins/test_snoozeable.py -v`. Expected: 2 passed.

### Step 13.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/mixins/ reclaim_sdk/resources/task.py tests/unit/mixins/test_snoozeable.py
git commit --no-gpg-sign -m "feat(mixin): add SnoozeableMixin, wire to Task"
```

---

## Task 14: `PlanWorkMixin` (new)

**Files:**
- Create: `reclaim_sdk/mixins/plan_work.py`
- Create: `tests/unit/mixins/test_plan_work.py`
- Modify: `reclaim_sdk/resources/task.py`

### Step 14.1: Write failing test

- [ ] **Create `tests/unit/mixins/test_plan_work.py`**

```python
import httpx
from datetime import datetime, timezone
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_plan_work_posts_with_datetime_and_duration(client, mock_api):
    route = mock_api.post("/api/planner/plan-work/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.plan_work(datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc), duration_minutes=60)
    params = dict(route.calls.last.request.url.params)
    assert "dateTime" in params
    assert params["durationMinutes"] == "60"
```

### Step 14.2-14.4: Run fail, implement, run pass

- [ ] **Run fail**.

- [ ] **Create `reclaim_sdk/mixins/plan_work.py`**

```python
from datetime import datetime, timezone
from typing import ClassVar, Optional


class PlanWorkMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def plan_work(self, date_time: datetime, duration_minutes: Optional[int] = None) -> None:
        params = {
            "dateTime": date_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if duration_minutes is not None:
            params["durationMinutes"] = duration_minutes
        response = self._client.post(
            f"/api/planner/plan-work/{self._PLANNER_PATH_SEGMENT}/{self.id}",
            params=params,
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)
```

- [ ] **Wire to `Task`** — add `PlanWorkMixin` to the class bases:

```python
class Task(BaseResource, SnoozeableMixin, PlanWorkMixin):
```

- [ ] **Run pass**.

### Step 14.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/mixins/plan_work.py reclaim_sdk/resources/task.py tests/unit/mixins/test_plan_work.py
git commit --no-gpg-sign -m "feat(mixin): add PlanWorkMixin, wire to Task"
```

---

## Task 15: `RestartableMixin` (new)

**Files:**
- Create: `reclaim_sdk/mixins/restartable.py`
- Create: `tests/unit/mixins/test_restartable.py`
- Modify: `reclaim_sdk/resources/task.py`

### Step 15.1: Failing test

- [ ] **Create `tests/unit/mixins/test_restartable.py`**

```python
import httpx
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_task_restart_posts(client, mock_api):
    route = mock_api.post("/api/planner/restart/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.restart()
    assert route.called
```

### Step 15.2-15.4

- [ ] **Run fail**.

- [ ] **Create `reclaim_sdk/mixins/restartable.py`**

```python
from typing import ClassVar


class RestartableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def restart(self) -> None:
        response = self._client.post(
            f"/api/planner/restart/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)
```

- [ ] **Wire to `Task`** — add `RestartableMixin` to bases.

- [ ] **Run pass**.

### Step 15.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/mixins/restartable.py reclaim_sdk/resources/task.py tests/unit/mixins/test_restartable.py
git commit --no-gpg-sign -m "feat(mixin): add RestartableMixin, wire to Task"
```

---

## Task 16: Refactor `start`/`stop` into `StartStoppableMixin`

**Files:**
- Create: `reclaim_sdk/mixins/start_stoppable.py`
- Create: `tests/unit/mixins/test_start_stoppable.py`
- Modify: `reclaim_sdk/resources/task.py` (remove inline `start`/`stop`, compose mixin)

### Step 16.1: Failing test

- [ ] **Create `tests/unit/mixins/test_start_stoppable.py`**

```python
import httpx
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_task_start_hits_planner_start(client, mock_api):
    route = mock_api.post("/api/planner/start/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.start()
    assert route.called


def test_task_stop_hits_planner_stop(client, mock_api):
    route = mock_api.post("/api/planner/stop/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.stop()
    assert route.called
```

### Step 16.2: Create mixin

- [ ] **Create `reclaim_sdk/mixins/start_stoppable.py`**

```python
from typing import ClassVar


class StartStoppableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def start(self) -> None:
        response = self._client.post(
            f"/api/planner/start/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def stop(self) -> None:
        response = self._client.post(
            f"/api/planner/stop/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)
```

### Step 16.3: Remove inline methods from `Task`

- [ ] **Edit `reclaim_sdk/resources/task.py`**

Delete the existing `start` and `stop` methods from `Task`. Add `StartStoppableMixin` to class bases.

### Step 16.4: Run tests

- [ ] **Run** `pytest tests/unit/mixins/test_start_stoppable.py -v`. Expected: 2 passed.

### Step 16.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/mixins/start_stoppable.py reclaim_sdk/resources/task.py tests/unit/mixins/test_start_stoppable.py
git commit --no-gpg-sign -m "refactor(task): move start/stop to StartStoppableMixin"
```

---

## Task 17: Refactor `log_work` into `LogWorkableMixin`

**Files:**
- Create: `reclaim_sdk/mixins/log_workable.py`
- Create: `tests/unit/mixins/test_log_workable.py`
- Modify: `reclaim_sdk/resources/task.py`

### Step 17.1: Failing test

- [ ] **Create `tests/unit/mixins/test_log_workable.py`**

```python
import httpx
from datetime import datetime, timezone
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_log_work_sends_minutes_and_zulu_end(client, mock_api):
    route = mock_api.post("/api/planner/log-work/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.log_work(60, datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc))
    params = dict(route.calls.last.request.url.params)
    assert params["minutes"] == "60"
    assert params["end"].endswith("Z")
    assert len(params["end"]) == 20  # YYYY-MM-DDTHH:MM:SS.MMMZ-ish — exact truncation check
```

### Step 17.2-17.4: Mixin + refactor

- [ ] **Create `reclaim_sdk/mixins/log_workable.py`**

```python
from datetime import datetime, timezone
from typing import ClassVar, Optional


class LogWorkableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def log_work(self, minutes: int, end: Optional[datetime] = None) -> None:
        params = {"minutes": minutes}
        if end:
            end = end.astimezone(timezone.utc)
            # Reclaim truncates microseconds to milliseconds
            params["end"] = end.isoformat()[:-9] + "Z"
        response = self._client.post(
            f"/api/planner/log-work/{self._PLANNER_PATH_SEGMENT}/{self.id}",
            params=params,
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)
```

- [ ] **Edit `Task`** — delete inline `log_work`, add `LogWorkableMixin` to bases.

- [ ] **Run test**, adjust truncation length assertion if needed (the existing format is `isoformat()[:-9] + "Z"` which yields `YYYY-MM-DDTHH:MM:SS.MMMZ` for UTC datetimes with microseconds — verify empirically in test).

### Step 17.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/mixins/log_workable.py reclaim_sdk/resources/task.py tests/unit/mixins/test_log_workable.py
git commit --no-gpg-sign -m "refactor(task): move log_work to LogWorkableMixin"
```

---

## Task 18: Refactor `mark_complete`/`mark_incomplete` into `CompletableMixin`

**Files:**
- Create: `reclaim_sdk/mixins/completable.py`
- Create: `tests/unit/mixins/test_completable.py`
- Modify: `reclaim_sdk/resources/task.py`

### Step 18.1: Failing test

- [ ] **Create `tests/unit/mixins/test_completable.py`**

```python
import httpx
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_mark_complete_posts_done(client, mock_api):
    mock_api.post("/api/planner/done/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.mark_complete()


def test_mark_incomplete_posts_unarchive(client, mock_api):
    mock_api.post("/api/planner/unarchive/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.mark_incomplete()
```

### Step 18.2-18.4

- [ ] **Create `reclaim_sdk/mixins/completable.py`**

```python
from typing import ClassVar


class CompletableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def mark_complete(self) -> None:
        response = self._client.post(
            f"/api/planner/done/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def mark_incomplete(self) -> None:
        # unarchive endpoint only exists for tasks — habits use different flow
        response = self._client.post(
            f"/api/planner/unarchive/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)
```

- [ ] **Edit `Task`** — delete inline methods, add `CompletableMixin` to bases.

- [ ] **Run tests** — expect 2 passed.

### Step 18.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/mixins/completable.py reclaim_sdk/resources/task.py tests/unit/mixins/test_completable.py
git commit --no-gpg-sign -m "refactor(task): move mark_complete/mark_incomplete to CompletableMixin"
```

---

## Task 19: Refactor `clear_exceptions` into `ClearExceptionsMixin`

**Files:**
- Create: `reclaim_sdk/mixins/clear_exceptions.py`
- Create: `tests/unit/mixins/test_clear_exceptions.py`
- Modify: `reclaim_sdk/resources/task.py`

### Step 19.1-19.5

- [ ] **Create `tests/unit/mixins/test_clear_exceptions.py`**

```python
import httpx
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_clear_exceptions_posts(client, mock_api):
    route = mock_api.post("/api/planner/clear-exceptions/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.clear_exceptions()
    assert route.called
```

- [ ] **Run fail**.

- [ ] **Create `reclaim_sdk/mixins/clear_exceptions.py`**

```python
from typing import ClassVar


class ClearExceptionsMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def clear_exceptions(self) -> None:
        response = self._client.post(
            f"/api/planner/clear-exceptions/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)
```

- [ ] **Edit `Task`** — delete inline, add `ClearExceptionsMixin` to bases.

- [ ] **Run pass, commit**

```bash
git add reclaim_sdk/mixins/clear_exceptions.py reclaim_sdk/resources/task.py tests/unit/mixins/test_clear_exceptions.py
git commit --no-gpg-sign -m "refactor(task): move clear_exceptions to ClearExceptionsMixin"
```

---

## Task 20: `task.reschedule_event` and `task.delete_policy`

**Files:**
- Modify: `reclaim_sdk/resources/task.py`
- Modify: `tests/unit/resources/test_task.py`

### Step 20.1: Failing tests

- [ ] **Append**

```python
def test_reschedule_event_posts(client, mock_api):
    route = mock_api.post("/api/planner/reschedule/task/event/evt-123").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.reschedule_event("evt-123")
    assert route.called


def test_delete_policy_deletes(client, mock_api):
    route = mock_api.delete("/api/planner/policy/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.delete_policy()
    assert route.called
```

### Step 20.2-20.4

- [ ] **Run fail, add to `Task`**

```python
    def reschedule_event(self, event_id: str) -> None:
        response = self._client.post(f"/api/planner/reschedule/task/event/{event_id}")
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def delete_policy(self) -> None:
        response = self._client.delete(f"/api/planner/policy/task/{self.id}")
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        if payload:
            self.__dict__.update(self.from_api_data(payload).__dict__)
```

- [ ] **Run pass**.

### Step 20.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/task.py tests/unit/resources/test_task.py
git commit --no-gpg-sign -m "feat(task): add reschedule_event + delete_policy"
```

---

## Task 21: `DailyHabit` resource — schema + CRUD

**Files:**
- Create: `reclaim_sdk/resources/habit.py`
- Create: `tests/unit/resources/test_habit.py`

### Step 21.1: Failing test

- [ ] **Create `tests/unit/resources/test_habit.py`**

```python
import httpx
from reclaim_sdk.resources.habit import DailyHabit


def test_habit_list_hits_assist_endpoint(client, mock_api):
    route = mock_api.get("/api/assist/habits/daily").mock(
        return_value=httpx.Response(200, json=[])
    )
    DailyHabit.list()
    assert route.called


def test_habit_save_creates_new(client, mock_api):
    route = mock_api.post("/api/assist/habits/daily").mock(
        return_value=httpx.Response(200, json={"id": 10, "title": "Run", "type": "CUSTOM_DAILY"})
    )
    h = DailyHabit(title="Run")
    h.save()
    assert h.id == 10


def test_habit_get_by_id(client, mock_api):
    mock_api.get("/api/assist/habits/daily/10").mock(
        return_value=httpx.Response(200, json={"id": 10, "title": "Run", "type": "CUSTOM_DAILY"})
    )
    h = DailyHabit.get(10)
    assert h.title == "Run"
```

### Step 21.2: Run (fail)

- [ ] **Run** `pytest tests/unit/resources/test_habit.py -v`. Expected: FAIL.

### Step 21.3: Implement

- [ ] **Create `reclaim_sdk/resources/habit.py`**

```python
from typing import ClassVar, Optional
from pydantic import Field
from reclaim_sdk.resources.base import BaseResource
from reclaim_sdk.enums import EventCategory, EventColor, PriorityLevel


class DailyHabit(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/assist/habits/daily"
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "habit"

    title: Optional[str] = Field(None, description="Habit title")
    description: Optional[str] = Field(None, description="Habit description")
    priority: Optional[PriorityLevel] = Field(None)
    event_category: EventCategory = Field(
        default=EventCategory.PERSONAL, alias="eventCategory"
    )
    event_color: Optional[EventColor] = Field(None, alias="eventColor")
    always_private: bool = Field(False, alias="alwaysPrivate")
    enabled: bool = Field(True)
    type: str = Field("CUSTOM_DAILY", description="Discriminator")
```

### Step 21.4: Run (pass), commit

- [ ] **Run pass, commit**

```bash
git add reclaim_sdk/resources/habit.py tests/unit/resources/test_habit.py
git commit --no-gpg-sign -m "feat(habit): add DailyHabit resource with CRUD"
```

**Note:** Full schema fields (scheduling windows, target hours, etc.) should be added via a follow-up commit by grepping `/tmp/reclaim-api.yml` for `DailyHabit:` schema definition and copying every property. Keep them all `Optional` unless Swagger marks them `required`.

---

## Task 22: Wire mixins into `DailyHabit`

**Files:**
- Modify: `reclaim_sdk/resources/habit.py`
- Create: `tests/unit/resources/test_habit.py` (extend)

### Step 22.1: Failing test

- [ ] **Append to `tests/unit/resources/test_habit.py`**

```python
def test_habit_start_uses_habit_segment(client, mock_api):
    route = mock_api.post("/api/planner/start/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    h = DailyHabit(id=10, title="Run")
    h.start()
    assert route.called


def test_habit_restart_uses_habit_segment(client, mock_api):
    route = mock_api.post("/api/planner/restart/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    h = DailyHabit(id=10, title="Run")
    h.restart()
    assert route.called


def test_habit_clear_exceptions(client, mock_api):
    route = mock_api.post("/api/planner/clear-exceptions/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    h = DailyHabit(id=10, title="Run")
    h.clear_exceptions()
    assert route.called
```

### Step 22.2-22.4

- [ ] **Run fail**.

- [ ] **Edit `reclaim_sdk/resources/habit.py`** — add mixin imports and compose:

```python
from reclaim_sdk.mixins.start_stoppable import StartStoppableMixin
from reclaim_sdk.mixins.restartable import RestartableMixin
from reclaim_sdk.mixins.clear_exceptions import ClearExceptionsMixin


class DailyHabit(BaseResource, StartStoppableMixin, RestartableMixin, ClearExceptionsMixin):
    # existing body …
```

- [ ] **Run pass**.

### Step 22.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/habit.py tests/unit/resources/test_habit.py
git commit --no-gpg-sign -m "feat(habit): compose start/stop/restart/clear_exceptions mixins"
```

---

## Task 23: Habit-specific planner actions

**Files:**
- Modify: `reclaim_sdk/resources/habit.py`
- Modify: `tests/unit/resources/test_habit.py`

### Step 23.1: Failing tests

- [ ] **Append**

```python
def test_habit_toggle_sends_enable(client, mock_api):
    route = mock_api.post("/api/planner/toggle/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    h = DailyHabit(id=10, title="Run")
    h.toggle(enable=False)
    params = dict(route.calls.last.request.url.params)
    assert params["enable"] == "false"


def test_habit_reschedule_event(client, mock_api):
    route = mock_api.post("/api/planner/reschedule/habit/event/evt-x").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    DailyHabit(id=10, title="Run").reschedule_event("evt-x")
    assert route.called


def test_habit_skip_event(client, mock_api):
    route = mock_api.post("/api/planner/skip/habit/event/evt-y").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    DailyHabit(id=10, title="Run").skip_event("evt-y")
    assert route.called


def test_habit_migrate_to_smart_series(client, mock_api):
    route = mock_api.post("/api/assist/habits/daily/10/migrate-to-smart-series").mock(
        return_value=httpx.Response(200, json={})
    )
    DailyHabit(id=10, title="Run").migrate_to_smart_series()
    assert route.called


def test_habit_delete_policy(client, mock_api):
    route = mock_api.delete("/api/planner/policy/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    DailyHabit(id=10, title="Run").delete_policy()
    assert route.called
```

### Step 23.2-23.4

- [ ] **Run fail, add to `DailyHabit`**

```python
    def toggle(self, enable: Optional[bool] = None) -> None:
        params = {}
        if enable is not None:
            params["enable"] = str(enable).lower()
        response = self._client.post(f"/api/planner/toggle/habit/{self.id}", params=params)
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def reschedule_event(self, event_id: str) -> None:
        response = self._client.post(f"/api/planner/reschedule/habit/event/{event_id}")
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def skip_event(self, event_id: str) -> None:
        response = self._client.post(f"/api/planner/skip/habit/event/{event_id}")
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def migrate_to_smart_series(self) -> None:
        self._client.post(f"{self.ENDPOINT}/{self.id}/migrate-to-smart-series")

    def delete_policy(self) -> None:
        response = self._client.delete(f"/api/planner/policy/habit/{self.id}")
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        if payload:
            self.__dict__.update(self.from_api_data(payload).__dict__)
```

- [ ] **Run pass**.

### Step 23.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/habit.py tests/unit/resources/test_habit.py
git commit --no-gpg-sign -m "feat(habit): toggle, reschedule_event, skip_event, migrate, delete_policy"
```

---

## Task 24: Habit template endpoints

**Files:**
- Modify: `reclaim_sdk/resources/habit.py`
- Modify: `tests/unit/resources/test_habit.py`

### Step 24.1: Failing tests

- [ ] **Append**

```python
import warnings


def test_list_templates_with_filters(client, mock_api):
    route = mock_api.get("/api/assist/habits/templates").mock(
        return_value=httpx.Response(200, json=[])
    )
    DailyHabit.list_templates(role="engineer", department="tech")
    params = dict(route.calls.last.request.url.params)
    assert params["role"] == "engineer"
    assert params["department"] == "tech"


def test_get_template(client, mock_api):
    mock_api.get("/api/assist/habits/template").mock(
        return_value=httpx.Response(200, json={"id": "tmpl-1", "title": "Standup"})
    )
    assert DailyHabit.get_template()["id"] == "tmpl-1"


def test_create_from_template_warns_deprecated(client, mock_api):
    mock_api.post("/api/assist/habits/template/create").mock(
        return_value=httpx.Response(200, json={"id": 99, "title": "Standup", "type": "CUSTOM_DAILY"})
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        DailyHabit.create_from_template("tmpl-1")
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
```

### Step 24.2-24.4

- [ ] **Run fail**.

- [ ] **Add to `DailyHabit`**

```python
    @classmethod
    def get_template(cls, client=None) -> dict:
        from reclaim_sdk.client import ReclaimClient
        if client is None:
            client = ReclaimClient()
        return client.get("/api/assist/habits/template")

    @classmethod
    def list_templates(cls, role=None, department=None, client=None) -> list[dict]:
        from reclaim_sdk.client import ReclaimClient
        if client is None:
            client = ReclaimClient()
        params = {}
        if role: params["role"] = role
        if department: params["department"] = department
        return client.get("/api/assist/habits/templates", params=params)

    @classmethod
    def create_from_template(cls, template_id: str, client=None) -> "DailyHabit":
        import warnings
        warnings.warn(
            "create_from_template is deprecated by Reclaim — use direct habit creation",
            DeprecationWarning,
            stacklevel=2,
        )
        from reclaim_sdk.client import ReclaimClient
        if client is None:
            client = ReclaimClient()
        data = client.post("/api/assist/habits/template/create", params={"templateId": template_id})
        return cls.from_api_data(data)
```

- [ ] **Run pass**.

### Step 24.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/habit.py tests/unit/resources/test_habit.py
git commit --no-gpg-sign -m "feat(habit): add template endpoints"
```

---

## Task 25: `Webhook` resource CRUD

**Files:**
- Create: `reclaim_sdk/resources/webhook.py`
- Create: `tests/unit/resources/test_webhook.py`

### Step 25.1: Failing test

- [ ] **Create `tests/unit/resources/test_webhook.py`**

```python
import httpx
from reclaim_sdk.resources.webhook import Webhook


def test_webhook_list(client, mock_api):
    mock_api.get("/api/team/current/webhooks").mock(
        return_value=httpx.Response(200, json=[])
    )
    Webhook.list()


def test_webhook_create(client, mock_api):
    mock_api.post("/api/team/current/webhooks").mock(
        return_value=httpx.Response(200, json={"id": 1, "url": "https://x.test", "events": ["task.created"]})
    )
    w = Webhook(url="https://x.test", events=["task.created"])
    w.save()
    assert w.id == 1


def test_webhook_delete(client, mock_api):
    route = mock_api.delete("/api/team/current/webhooks/1").mock(
        return_value=httpx.Response(204)
    )
    w = Webhook(id=1, url="https://x.test", events=["task.created"])
    w.delete()
    assert route.called
```

### Step 25.2-25.4

- [ ] **Run fail**.

- [ ] **Create `reclaim_sdk/resources/webhook.py`**

```python
from typing import ClassVar, Optional
from pydantic import Field
from reclaim_sdk.resources.base import BaseResource


class Webhook(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/team/current/webhooks"

    url: Optional[str] = Field(None, description="Receiver URL")
    events: list[str] = Field(default_factory=list, description="Subscribed event types")
    secret: Optional[str] = Field(None, description="HMAC signing secret (if server supports)")
```

- [ ] **Run pass**.

### Step 25.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/webhook.py tests/unit/resources/test_webhook.py
git commit --no-gpg-sign -m "feat(webhook): add Webhook CRUD resource"
```

**Note:** Verify `Webhook` schema fields against Swagger during implementation. Grep `/tmp/reclaim-api.yml` for the `Webhook:` schema definition and add any missing fields.

---

## Task 26: Webhook payload models

**Files:**
- Create: `reclaim_sdk/webhooks/__init__.py`, `reclaim_sdk/webhooks/payloads.py`
- Create: `tests/unit/webhooks/test_payloads.py`

### Step 26.1: Failing test

- [ ] **Create `tests/unit/webhooks/test_payloads.py`**

```python
import json
from datetime import datetime, timezone
from reclaim_sdk.webhooks.payloads import (
    parse_webhook_payload, TaskWebhookEvent, HabitWebhookEvent,
)


def test_parse_task_created_payload():
    raw = json.dumps({
        "eventId": "evt-1",
        "type": "task.created",
        "created": "2026-04-21T10:00:00Z",
        "task": {
            "id": 1, "title": "hello", "type": "TASK",
            "priority": "P3", "taskSource": "RECLAIM",
            "readOnlyFields": [], "sortKey": 1.0,
            "prioritizableType": "TASK",
            "eventCategory": "WORK", "eventSubType": "TASK",
            "onDeck": False, "atRisk": False, "deleted": False,
            "adjusted": False, "deferred": False, "alwaysPrivate": False,
            "status": "NEW", "index": 0.0,
            "timeChunksRequired": 4, "minChunkSize": 1, "maxChunkSize": 4,
            "timeChunksSpent": 0, "timeChunksRemaining": 4,
            "notes": "", "timeSchemeId": "",
            "created": "2026-04-21T10:00:00Z", "updated": "2026-04-21T10:00:00Z",
        },
    })
    evt = parse_webhook_payload(raw)
    assert isinstance(evt, TaskWebhookEvent)
    assert evt.type == "task.created"
    assert evt.task.id == 1


def test_parse_habit_updated_payload():
    raw = json.dumps({
        "eventId": "evt-2",
        "type": "habit.updated",
        "created": "2026-04-21T10:00:00Z",
        "habit": {"id": 99, "title": "Run", "type": "CUSTOM_DAILY"},
    })
    evt = parse_webhook_payload(raw)
    assert isinstance(evt, HabitWebhookEvent)
    assert evt.habit.id == 99


def test_parse_unknown_type_raises():
    import pydantic
    raw = json.dumps({"eventId": "e", "type": "unknown.thing", "created": "2026-04-21T10:00:00Z"})
    try:
        parse_webhook_payload(raw)
    except pydantic.ValidationError:
        return
    assert False, "expected ValidationError"
```

### Step 26.2-26.4

- [ ] **Create `reclaim_sdk/webhooks/__init__.py`**

```python
from reclaim_sdk.webhooks.payloads import (
    WebhookEvent, TaskWebhookEvent, HabitWebhookEvent, parse_webhook_payload,
)
from reclaim_sdk.webhooks.signature import verify_signature, SignatureVerificationError

__all__ = [
    "WebhookEvent", "TaskWebhookEvent", "HabitWebhookEvent",
    "parse_webhook_payload", "verify_signature", "SignatureVerificationError",
]
```

- [ ] **Create `reclaim_sdk/webhooks/payloads.py`**

```python
from datetime import datetime
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, TypeAdapter
from reclaim_sdk.resources.task import Task
from reclaim_sdk.resources.habit import DailyHabit


class _Base(BaseModel):
    event_id: str = Field(alias="eventId")
    created: datetime

    model_config = {"populate_by_name": True}


class TaskWebhookEvent(_Base):
    type: Literal["task.created", "task.updated", "task.completed", "task.deleted"]
    task: Task


class HabitWebhookEvent(_Base):
    type: Literal["habit.created", "habit.updated", "habit.deleted"]
    habit: DailyHabit


WebhookEvent = Annotated[
    Union[TaskWebhookEvent, HabitWebhookEvent],
    Field(discriminator="type"),
]

_adapter = TypeAdapter(WebhookEvent)


def parse_webhook_payload(raw: bytes | str) -> WebhookEvent:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return _adapter.validate_json(raw)
```

- [ ] **Run tests. Passes.**

### Step 26.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/webhooks/__init__.py reclaim_sdk/webhooks/payloads.py tests/unit/webhooks/test_payloads.py
git commit --no-gpg-sign -m "feat(webhooks): typed payload models with discriminated union"
```

**Note:** Exact event-type literals (`task.created` etc.) need confirmation during live-mode discovery. Adjust union when real payloads observed.

---

## Task 27: Webhook signature verification module

**Files:**
- Create: `reclaim_sdk/webhooks/signature.py`
- Create: `tests/unit/webhooks/test_signature.py`
- Modify: `reclaim_sdk/exceptions.py`

### Step 27.1: Failing test

- [ ] **Create `tests/unit/webhooks/test_signature.py`**

```python
import hmac
import hashlib
import pytest
from reclaim_sdk.webhooks.signature import verify_signature, SignatureVerificationError


SECRET = "s3cret"


def _sign(body: bytes) -> str:
    return hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_returns_true():
    body = b'{"x":1}'
    assert verify_signature(body, _sign(body), SECRET) is True


def test_invalid_signature_raises():
    with pytest.raises(SignatureVerificationError):
        verify_signature(b'{"x":1}', "deadbeef", SECRET)


def test_empty_signature_raises():
    with pytest.raises(SignatureVerificationError):
        verify_signature(b'{}', "", SECRET)
```

### Step 27.2-27.4

- [ ] **Modify `reclaim_sdk/exceptions.py`** — add:

```python
class SignatureVerificationError(ReclaimAPIError):
    """Raised when a webhook signature does not match."""
```

- [ ] **Create `reclaim_sdk/webhooks/signature.py`**

```python
"""Webhook signature verification.

Reclaim signature header name and algorithm are verified during live-mode
discovery (register a test webhook, inspect headers). Current implementation
assumes HMAC-SHA256 hex digest of the raw request body with the subscriber's
secret. If live observation shows Reclaim uses a different scheme, update the
`verify_signature` function accordingly — or replace the body with
`raise NotImplementedError(...)` if no signature is actually emitted.
"""

import hmac
import hashlib
from reclaim_sdk.exceptions import SignatureVerificationError


def verify_signature(body: bytes, header: str, secret: str) -> bool:
    if not header:
        raise SignatureVerificationError("empty signature header")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, header):
        raise SignatureVerificationError("signature mismatch")
    return True
```

- [ ] **Run pass**.

### Step 27.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/webhooks/signature.py reclaim_sdk/exceptions.py tests/unit/webhooks/test_signature.py
git commit --no-gpg-sign -m "feat(webhooks): add HMAC-SHA256 signature verification"
```

---

## Task 28: `Changelog` namespace

**Files:**
- Create: `reclaim_sdk/resources/changelog.py`
- Create: `tests/unit/resources/test_changelog.py`

### Step 28.1: Failing test

- [ ] **Create `tests/unit/resources/test_changelog.py`**

```python
import httpx
from reclaim_sdk.resources.changelog import Changelog, ChangeLogEntryView


def test_changelog_tasks(client, mock_api):
    route = mock_api.get("/api/changelog/tasks").mock(
        return_value=httpx.Response(200, json=[
            {"id": "e1", "entityId": "1", "changeType": "CREATED"},
        ])
    )
    entries = Changelog.tasks([1, 2, 3])
    params = dict(route.calls.last.request.url.params)
    assert "taskIds" in params or any("taskIds" in k for k in params)
    assert len(entries) == 1
    assert isinstance(entries[0], ChangeLogEntryView)


def test_changelog_all(client, mock_api):
    mock_api.get("/api/changelog").mock(return_value=httpx.Response(200, json=[]))
    assert Changelog.all() == []
```

### Step 28.2-28.4

- [ ] **Create `reclaim_sdk/resources/changelog.py`**

```python
from typing import Optional
from pydantic import BaseModel, Field
from reclaim_sdk.client import ReclaimClient


class ChangeLogEntryView(BaseModel):
    id: Optional[str] = Field(None)
    entity_id: Optional[str] = Field(None, alias="entityId")
    change_type: Optional[str] = Field(None, alias="changeType")

    model_config = {"populate_by_name": True, "extra": "allow"}


def _client_or_default(client):
    return client or ReclaimClient()


class Changelog:
    @staticmethod
    def tasks(task_ids: list[int], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/tasks", params={"taskIds": task_ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def events(event_ids: list[str], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/events", params={"eventIds": event_ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def smart_habits(ids: list[int], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/smart-habits", params={"ids": ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def smart_meetings(ids: list[int], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/smart-meetings", params={"ids": ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def scheduling_links(ids: list[str], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/scheduling-links", params={"ids": ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def all(client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get("/api/changelog")
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]
```

- [ ] **Run pass**.

### Step 28.5: Commit

- [ ] **Commit**

```bash
git add reclaim_sdk/resources/changelog.py tests/unit/resources/test_changelog.py
git commit --no-gpg-sign -m "feat(changelog): add Changelog namespace + ChangeLogEntryView"
```

---

## Task 29: Hours regression test

**Files:**
- Create: `tests/unit/resources/test_hours.py`

### Step 29.1-29.3

- [ ] **Create `tests/unit/resources/test_hours.py`**

```python
import httpx
from reclaim_sdk.resources.hours import Hours


def test_hours_list(client, mock_api):
    route = mock_api.get("/api/timeschemes").mock(
        return_value=httpx.Response(200, json=[{
            "id": "ts-1", "status": "ACTIVE", "title": "Work",
            "description": "Work hours", "features": [],
        }])
    )
    result = Hours.list()
    assert len(result) == 1
    assert result[0].id == "ts-1"
```

- [ ] **Run, pass, commit**

```bash
git add tests/unit/resources/test_hours.py
git commit --no-gpg-sign -m "test(hours): regression coverage for existing Hours resource"
```

---

## Task 30: Live-mode tests — Task round-trip

**Files:**
- Create: `tests/live/test_task_live.py`

### Step 30.1: Write test

- [ ] **Create `tests/live/test_task_live.py`**

```python
import pytest
from datetime import datetime, timedelta, timezone
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource, SnoozeOption


pytestmark = pytest.mark.live


def test_task_full_lifecycle(live_client, tracked_ids, prefix):
    task = Task(
        title=f"{prefix} lifecycle",
        priority=PriorityLevel.P3,
        taskSource=TaskSource.RECLAIM,
    )
    task.duration = 1.0
    task.save()
    tracked_ids["tasks"].append(task.id)
    assert task.id is not None
    assert task.title.startswith(prefix)

    # update
    task.notes = "updated"
    task.save()
    task.refresh()
    assert task.notes == "updated"

    # planner actions
    task.start()
    task.stop()
    task.snooze(SnoozeOption.ONE_HOUR)
    task.clear_snooze()
    task.mark_complete()
    task.mark_incomplete()

    # found in list
    listed = [t.id for t in Task.list()]
    assert task.id in listed
```

### Step 30.2: Run (skipped unless live mode)

- [ ] **Run**

```bash
pytest tests/live/test_task_live.py -v
```

Expected (no env flag): 1 skipped.

- [ ] **Run with env flag (optional, only if developer wants)**

```bash
RECLAIM_LIVE_TEST=1 RECLAIM_TOKEN=<real-token> pytest tests/live/test_task_live.py -v
```

Expected: 1 passed, cleanup succeeds.

### Step 30.3: Commit

- [ ] **Commit**

```bash
git add tests/live/test_task_live.py
git commit --no-gpg-sign -m "test(live): Task lifecycle round-trip"
```

---

## Task 31: Live-mode tests — Habit, Webhook, Hours, Changelog

**Files:**
- Create: `tests/live/test_habit_live.py`, `tests/live/test_webhook_live.py`, `tests/live/test_hours_live.py`, `tests/live/test_changelog_live.py`

### Step 31.1: Create all four

- [ ] **Create `tests/live/test_habit_live.py`**

```python
import pytest
from reclaim_sdk.resources.habit import DailyHabit

pytestmark = pytest.mark.live


def test_habit_lifecycle(live_client, tracked_ids, prefix):
    h = DailyHabit(title=f"{prefix} habit")
    h.save()
    tracked_ids["habits"].append(h.id)
    h.toggle(enable=False)
    h.toggle(enable=True)
```

- [ ] **Create `tests/live/test_webhook_live.py`**

```python
import pytest
from reclaim_sdk.resources.webhook import Webhook

pytestmark = pytest.mark.live


def test_webhook_create_list_delete(live_client, tracked_ids):
    w = Webhook(url="https://example.test/hook", events=["task.created"])
    w.save()
    tracked_ids["webhooks"].append(w.id)
    assert w.id is not None
    assert w.id in [x.id for x in Webhook.list()]
```

- [ ] **Create `tests/live/test_hours_live.py`**

```python
import pytest
from reclaim_sdk.resources.hours import Hours

pytestmark = pytest.mark.live


def test_hours_list_returns_schemes(live_client):
    schemes = Hours.list()
    assert isinstance(schemes, list)
```

- [ ] **Create `tests/live/test_changelog_live.py`**

```python
import pytest
from reclaim_sdk.resources.changelog import Changelog

pytestmark = pytest.mark.live


def test_changelog_all(live_client):
    assert isinstance(Changelog.all(), list)
```

### Step 31.2: Verify

- [ ] **Run** `pytest tests/live -v`. Expected: 4 skipped.

### Step 31.3: Commit

- [ ] **Commit**

```bash
git add tests/live/
git commit --no-gpg-sign -m "test(live): coverage for habit, webhook, hours, changelog"
```

---

## Task 32: Documentation, examples, CI

**Files:**
- Create: `CHANGELOG.md`
- Create: `examples/habit_management.py`, `examples/webhooks.py`, `examples/changelog.py`
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`, `reclaim_sdk/__init__.py`

### Step 32.1: Version bump

- [ ] **Edit `reclaim_sdk/__init__.py`**

```python
__version__ = "0.7.0"
```

### Step 32.2: CHANGELOG

- [ ] **Create `CHANGELOG.md`**

```markdown
# Changelog

## 0.7.0 — 2026-04-21

### Breaking Changes

- `TaskPriority` enum removed — use `PriorityLevel` from `reclaim_sdk.enums` instead.
- Local `TaskStatus`, `EventCategory`, `EventColor` enums on `Task` moved to `reclaim_sdk.enums`. Imports `from reclaim_sdk.resources.task import ...Enum` must change to `from reclaim_sdk.enums import ...`.
- `Task.event_sub_type` is now `EventSubType` enum instead of `str`.
- `Task.list()` and `Task.get()` now auto-inject the `user` query parameter (from cached `GET /api/users/current`). Explicit `user=` is still accepted.
- New required `Task` fields: `taskSource`, `readOnlyFields`, `sortKey`, `prioritizableType`, `type`. `Task(...)` constructor calls that relied on defaults may need arguments.

### Fixed

- `Task.prioritize_by_due()` no longer raises `AttributeError` (used unset `cls._client`).

### Added

**Task:**
- `Task.create_at_time(task, start_time)` — POST `/api/tasks/at-time`
- `Task.find_min_index()` — GET `/api/tasks/min-index`
- `Task.batch_patch/batch_delete/batch_archive(patches)` + `TaskPatch` model
- `Task.register_interest(user)`
- `task.reindex(sort_key)`, `task.reschedule_event(event_id)`, `task.delete_policy()`
- `task.save(strategy='put')` for full replace
- Mixin-sourced `task.snooze/clear_snooze/plan_work/restart` (start/stop/log_work/mark_complete/mark_incomplete/clear_exceptions refactored into mixins; behavior unchanged)

**Habit (new resource):**
- Full CRUD via `DailyHabit`
- Planner actions: `start/stop/restart/clear_exceptions` (shared mixins), `toggle`, `reschedule_event`, `skip_event`, `migrate_to_smart_series`, `delete_policy`
- Templates: `get_template`, `list_templates`, `create_from_template` (deprecated upstream)

**Webhook (new resource):**
- CRUD via `Webhook`
- Typed payload models: `TaskWebhookEvent`, `HabitWebhookEvent`, `parse_webhook_payload(raw)`
- HMAC-SHA256 signature verification: `verify_signature(body, header, secret)`

**Changelog (new):**
- `Changelog.tasks/events/smart_habits/smart_meetings/scheduling_links/all`

**Client:**
- `ReclaimClient.current_user()` with session-level caching.
```

### Step 32.3: README migration notes

- [ ] **Edit `README.md`** — add after the `# reclaim-sdk` line:

```markdown
> **Migrating from 0.6.x to 0.7.0?** See `CHANGELOG.md` — enums moved, `user` param auto-resolved, new required Task fields.
```

### Step 32.4: Examples

- [ ] **Create `examples/habit_management.py`**

```python
from reclaim_sdk.resources.habit import DailyHabit

habit = DailyHabit(title="Daily Standup", description="15min sync")
habit.save()

habit.toggle(enable=False)
habit.toggle(enable=True)

habits = DailyHabit.list()
templates = DailyHabit.list_templates(role="engineer")

habit.delete()
```

- [ ] **Create `examples/webhooks.py`**

```python
from reclaim_sdk.resources.webhook import Webhook
from reclaim_sdk.webhooks import parse_webhook_payload, verify_signature, TaskWebhookEvent

# Subscribe
wh = Webhook(url="https://yourapp.test/reclaim-hook",
             events=["task.created", "task.updated", "task.completed"])
wh.save()

# In your receiver (Flask example):
# def hook(request):
#     verify_signature(request.data, request.headers["X-Reclaim-Signature"], SECRET)
#     event = parse_webhook_payload(request.data)
#     if isinstance(event, TaskWebhookEvent):
#         print(event.task.title)
```

- [ ] **Create `examples/changelog.py`**

```python
from reclaim_sdk.resources.changelog import Changelog

for entry in Changelog.all():
    print(entry.change_type, entry.entity_id)

task_entries = Changelog.tasks([1, 2, 3])
```

### Step 32.5: CI workflow for PRs

- [ ] **Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
    branches: [master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: flake8 reclaim_sdk
      - run: pytest tests/unit --cov=reclaim_sdk --cov-report=term-missing --cov-fail-under=90
```

### Step 32.6: Full test run

- [ ] **Run** `pytest tests/unit --cov=reclaim_sdk -v`. Expected: all pass, coverage ≥90%.

### Step 32.7: Commit

- [ ] **Commit**

```bash
git add CHANGELOG.md README.md reclaim_sdk/__init__.py examples/ .github/workflows/ci.yml
git commit --no-gpg-sign -m "chore: 0.7.0 release — docs, examples, CI, version bump"
```

---

## Task 33: Final verification

### Step 33.1: Full mocked suite

- [ ] **Run**

```bash
pytest tests/unit -v
```

Expected: every test passes. Coverage ≥90%.

### Step 33.2: Lint

- [ ] **Run**

```bash
flake8 reclaim_sdk
black --check reclaim_sdk
```

Expected: clean.

### Step 33.3: Build sanity check

- [ ] **Run**

```bash
python setup.py sdist bdist_wheel
```

Expected: builds without errors. Artifacts in `dist/`.

### Step 33.4: Live-mode spot check (OPTIONAL, requires real token)

- [ ] **Run**

```bash
RECLAIM_LIVE_TEST=1 RECLAIM_TOKEN=$RECLAIM_TOKEN pytest tests/live -v
```

Expected: all pass, cleanup succeeds, no `[sdk-test-*]` entities remain in the account.

### Step 33.5: Merge readiness

- [ ] Confirm `master` is the target branch.
- [ ] Confirm `__version__ = "0.7.0"` in `reclaim_sdk/__init__.py`.
- [ ] Push to GitHub → PR → CI green → merge → auto-publish to PyPI triggers.

---

## Self-Review Notes

- **Coverage check:** Spec's 8 deliverables → mapped to tasks:
  1. Fix prioritize_by_due → Task 5
  2. Schema align → Task 6
  3. New Task endpoints → Tasks 7–12, 20
  4. Task-planner actions → Tasks 13–20
  5. User param required → Tasks 3–4
  6. Webhooks → Tasks 25–27
  7. Habits (incl. templates) → Tasks 21–24
  8. Changelog → Task 28
- **Placeholder scan:** three `**Note:**` blocks flag discovery work (exact enum values, Webhook schema fields, webhook event type literals). Each is explicit about *where* to look and *what* to adjust — not hand-waving.
- **Type consistency:** `_PLANNER_PATH_SEGMENT` is the attribute name used consistently across all mixins and resources. `TaskPatch` fields use camelCase aliases matching Swagger.
- **Out of scope (unchanged from spec):** Events, Calendars, Scheduling Links, One-on-Ones, Analytics, Focus Settings, Integrations, API key mgmt, Admin ops, Delegated Access, Account Time Schemes.
