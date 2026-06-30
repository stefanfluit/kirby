from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CoverageResult:
    num_changed: int
    num_tested: int
    not_tested: list[str]
    num_failed_tests: int


class CoverageTracker:
    """Track which changed Ansible tasks have passing Serverspec coverage."""

    def __init__(self) -> None:
        self._num_changed: int = 0
        self._num_tested: int = 0
        self._not_tested: list[str] = []

    def record_task(self, task_name: str, prev_failed: int, curr_failed: int) -> None:
        self._num_changed += 1
        if curr_failed < prev_failed:
            self._num_tested += 1
        else:
            self._not_tested.append(task_name)

    @property
    def coverage_pct(self) -> float:
        if self._num_changed == 0:
            return 0.0
        return self._num_tested * 100.0 / self._num_changed

    def result(self, num_failed_tests: int) -> CoverageResult:
        return CoverageResult(
            num_changed=self._num_changed,
            num_tested=self._num_tested,
            not_tested=list(self._not_tested),
            num_failed_tests=num_failed_tests,
        )
