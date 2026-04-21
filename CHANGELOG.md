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
