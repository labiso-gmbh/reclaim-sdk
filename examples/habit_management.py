"""Habit management example.

Note: habit creation via API frequently returns 409 Conflict due to scheduling
collisions with existing calendar events or plan-tier limits. In practice, most
users create habits via the web app and then manage them (toggle, reschedule,
skip) via the SDK.
"""

from reclaim_sdk.resources.habit import DailyHabit

# List existing habits
habits = DailyHabit.list()
for h in habits:
    print(f"{h.id}: {h.title} (enabled={h.enabled})")

# Pause the first ENABLED habit, then re-enable it.
# Toggling to the current state returns 409 Conflict.
active = next((h for h in habits if h.enabled), None)
if active:
    active.toggle(enable=False)
    print(f"Paused {active.title}")
    active.toggle(enable=True)
    print(f"Resumed {active.title}")

# Fetch available templates (for users creating habits in bulk).
# Note: template creation (`create_from_template`) is deprecated upstream.
templates = DailyHabit.list_templates()
print(f"{len(templates)} templates available")
