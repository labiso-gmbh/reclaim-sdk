from typing import ClassVar


class ClearExceptionsMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def clear_exceptions(self) -> None:
        response = self._client.post(
            f"/api/planner/clear-exceptions/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = (
            response.get("taskOrHabit", response)
            if isinstance(response, dict)
            else response
        )
        self.__dict__.update(self.from_api_data(payload).__dict__)
