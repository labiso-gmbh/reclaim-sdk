from reclaim_sdk.resources.habit import DailyHabit

habit = DailyHabit(title="Daily Standup", description="15min sync")
habit.save()

habit.toggle(enable=False)
habit.toggle(enable=True)

habits = DailyHabit.list()
templates = DailyHabit.list_templates(role="engineer")

habit.delete()
