from typing import ClassVar


class StartStoppableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def start(self) -> None:
        response = self._client.post(
            f"/api/planner/start/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = (
            response.get("taskOrHabit", response)
            if isinstance(response, dict)
            else response
        )
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def stop(self) -> None:
        response = self._client.post(
            f"/api/planner/stop/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = (
            response.get("taskOrHabit", response)
            if isinstance(response, dict)
            else response
        )
        self.__dict__.update(self.from_api_data(payload).__dict__)
