# Changelog

## 0.8.0 — 2026-05-07

### Breaking Changes

- `Hours.id` is now `Optional[str]` (UUID) instead of inheriting `Optional[int]` from `BaseResource`. Time schemes have always been UUIDs server-side; the previous integer hint was wrong.
- `Hours.task_target_calendar` field reinstated as a read-only mirror of the server-resolved calendar object. To set the target calendar on create/update, use the new `task_target_calendar_id: int` field — that's what the API actually accepts.

### Added

**Hours / time schemes — full CRUD against `/api/timeschemes`:**
- `Hours.policy_type: PolicyType` — `CUSTOM`, `WORK`, `PERSONAL`, `MEETING`
- `Hours.policy: TimeSchemePolicy` with `day_hours: dict[Weekday, DayIntervals]` — required for `policy_type=CUSTOM`
- New nested models: `TimeSchemePolicy`, `DayIntervals`, `Interval` (HH:MM:SS time strings)
- New enums: `Weekday`, `TimeSchemeFeature`, `PolicyType`
- `Hours.task_target_calendar_id: int` — calendar where scheduled events land
- `examples/hours.py` — end-to-end CRUD demo

**Client:**
- `ReclaimClient` JSON encoder now also serialises `datetime.time` (HH:MM:SS) and `datetime.date` (ISO 8601), needed by `Hours.policy.day_hours` intervals.

### Fixed

- README + project docs no longer claim `Hours` is a read-only list — basic CRUD was always inherited from `BaseResource`, but the model was too thin (6 fields) to send a usable payload. Schema reverse-engineered from `app.reclaim.ai` network captures.

## 0.7.1 — 2026-04-22

### Fixed

- `ReclaimClient.configure(token, base_url=...)` now actually applies the supplied `base_url`. Previously the argument was silently dropped and the client always pointed at production (`https://api.app.reclaim.ai`).
- `LogWorkableMixin.log_work(end=...)` (used by `Task.log_work`) now formats `end` as `YYYY-MM-DDTHH:MM:SS.mmmZ` for any input. Previously, datetimes with `microsecond == 0` had their seconds silently dropped (`YYYY-MM-DDTHH:MMZ`) due to a fixed-width `isoformat()[:-9]` slice.

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
