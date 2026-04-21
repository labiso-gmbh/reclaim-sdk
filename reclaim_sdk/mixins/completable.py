from typing import ClassVar


class CompletableMixin:
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    def mark_complete(self) -> None:
        response = self._client.post(
            f"/api/planner/done/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = (
            response.get("taskOrHabit", response)
            if isinstance(response, dict)
            else response
        )
        self.__dict__.update(self.from_api_data(payload).__dict__)

    def mark_incomplete(self) -> None:
        # unarchive endpoint only exists for tasks — habits use different flow
        response = self._client.post(
            f"/api/planner/unarchive/{self._PLANNER_PATH_SEGMENT}/{self.id}"
        )
        payload = (
            response.get("taskOrHabit", response)
            if isinstance(response, dict)
            else response
        )
        self.__dict__.update(self.from_api_data(payload).__dict__)
