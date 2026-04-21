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
            params["relativeFrom"] = (
                relative_from.astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
        response = self._client.post(
            f"/api/planner/{self._PLANNER_PATH_SEGMENT}/{self.id}/snooze",
            params=params,
        )
        payload = (
            response.get("taskOrHabit", response)
            if isinstance(response, dict)
            else response
        )
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def clear_snooze(self) -> None:
        response = self._client.post(
            f"/api/planner/{self._PLANNER_PATH_SEGMENT}/{self.id}/clear-snooze"
        )
        payload = (
            response.get("taskOrHabit", response)
            if isinstance(response, dict)
            else response
        )
        self.__dict__.update(self.from_api_data(payload).__dict__)
