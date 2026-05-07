"""Time scheme (Hours) CRUD example.

A *time scheme* is a named working-hours profile. Reclaim ships built-in
schemes (Work, Personal, Meeting) and lets users create their own. This
example creates a custom 9-to-5 Mon-Fri scheme, edits it, and deletes it.

Run with::

    RECLAIM_TOKEN=... python examples/hours.py
"""

from datetime import time

from reclaim_sdk.enums import PolicyType, TimeSchemeFeature, Weekday
from reclaim_sdk.resources.hours import (
    DayIntervals,
    Hours,
    Interval,
    TimeSchemePolicy,
)


def main() -> None:
    # 1) List existing schemes
    print("Existing schemes:")
    for scheme in Hours.list():
        print(f"  {scheme.id}  [{scheme.policy_type}]  {scheme.title}")

    # 2) Build a Mon-Fri 9-to-5 custom scheme
    workday = DayIntervals(
        intervals=[
            Interval(start=time(9, 0), end=time(17, 0)),
        ]
    )
    new = Hours(
        title="Demo Hours",
        description="Created from the SDK example",
        task_category="WORK",
        policy_type=PolicyType.CUSTOM,
        policy=TimeSchemePolicy(
            day_hours={
                Weekday.MONDAY: workday,
                Weekday.TUESDAY: workday,
                Weekday.WEDNESDAY: workday,
                Weekday.THURSDAY: workday,
                Weekday.FRIDAY: workday,
            }
        ),
        features=[
            TimeSchemeFeature.TASK_ASSIGNMENT,
            TimeSchemeFeature.HABIT_ASSIGNMENT,
        ],
    )
    new.save()
    print(f"\nCreated: {new.id}  {new.title}")

    # 3) Edit it
    new.description = "Updated by the SDK example"
    new.save()
    print(f"Updated description: {new.description!r}")

    # 4) Clean up
    new.delete()
    print(f"Deleted: {new.id}")


if __name__ == "__main__":
    main()
