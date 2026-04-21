from reclaim_sdk.resources.changelog import Changelog

for entry in Changelog.all():
    print(entry.change_type, entry.entity_id)

task_entries = Changelog.tasks([1, 2, 3])
