from typing import ClassVar


class RestartableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def restart(self) -> None:
        response = self._client.post(
            f"/api/planner/restart/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = response.get("taskOrHabit", response) if isinstance(response, dict) else response
        self.__dict__.update(self.from_api_data(payload).__dict__)
