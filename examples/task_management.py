from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, EventColor
from reclaim_sdk.resources.hours import Hours
from reclaim_sdk.exceptions import (
    RecordNotFound,
    InvalidRecord,
    AuthenticationError,
    ReclaimAPIError,
)
from datetime import datetime

try:
    # Create a new task
    task = Task(
        title="My new task",
        due=datetime(2023, 12, 31),
        priority=PriorityLevel.P3,
    )

    # Those are set via properties, so we can't set them directly
    # in the dataclass
    task.duration = 3.0
    task.max_work_duration = 1.5
    task.min_work_duration = 0.5
    task.save()

    # Update the description
    task.notes = "Updated description"
    task.event_color = EventColor.BANANA
    task.save()

    # Change the task to use custom hour scheme
    all_hours = Hours.list()
    task.time_scheme_id = all_hours[2].id
    task.save()

    # Add time to the task
    task.add_time(0.5)  # Add 30 minutes

    # Set the task to be in the up next list
    task.up_next = True
    task.save()

    # Start the task
    task.start()

    # Log work on the task
    task.log_work(60, datetime.now())

    # Stop the task
    task.stop()

    # Mark the task as complete
    task.mark_complete()

    # Mark the task as incomplete
    task.mark_incomplete()

    # List all tasks
    all_tasks = Task.list()


except RecordNotFound as e:
    print(f"Record not found: {e}")
except InvalidRecord as e:
    print(f"Invalid record: {e}")
except AuthenticationError as e:
    print(f"Authentication error: {e}")
except ReclaimAPIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Clean up
    if task:
        task.delete()
