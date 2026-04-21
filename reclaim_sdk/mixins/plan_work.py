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
