from datetime import datetime, timezone
from typing import ClassVar, Optional


class LogWorkableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def log_work(self, minutes: int, end: Optional[datetime] = None) -> None:
        params = {"minutes": minutes}
        if end:
            # Reclaim expects millisecond precision in Zulu format.
            # `isoformat(timespec="milliseconds")` is robust regardless of input microsecond.
            end_utc_naive = end.astimezone(timezone.utc).replace(tzinfo=None)
            params["end"] = end_utc_naive.isoformat(timespec="milliseconds") + "Z"
        response = self._client.post(
            f"/api/planner/log-work/{self._PLANNER_PATH_SEGMENT}/{self.id}",
            params=params,
        )
        payload = (
            response.get("taskOrHabit", response)
            if isinstance(response, dict)
            else response
        )
        self.__dict__.update(self.from_api_data(payload).__dict__)
