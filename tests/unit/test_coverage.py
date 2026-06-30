from __future__ import annotations

from ansible_collections.stefanfluit.kirby.plugins.module_utils.coverage import (
    CoverageResult,
    CoverageTracker,
)


class TestCoverageTracker:
    def test_initial_state_has_zero_counts(self) -> None:
        tracker = CoverageTracker()
        result = tracker.result(0)
        assert result == CoverageResult(
            num_changed=0, num_tested=0, not_tested=[], num_failed_tests=0
        )

    def test_coverage_pct_is_zero_with_no_tasks(self) -> None:
        assert CoverageTracker().coverage_pct == 0.0

    def test_tested_task_increments_num_tested(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("task1", prev_failed=2, curr_failed=1)
        assert tracker._num_tested == 1
        assert tracker._not_tested == []

    def test_untested_task_added_to_not_tested(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("task1", prev_failed=1, curr_failed=1)
        assert tracker._num_tested == 0
        assert tracker._not_tested == ["task1"]

    def test_coverage_100_percent(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("task1", prev_failed=2, curr_failed=1)
        assert tracker.coverage_pct == 100.0

    def test_coverage_50_percent(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("task1", prev_failed=2, curr_failed=1)
        tracker.record_task("task2", prev_failed=1, curr_failed=1)
        assert tracker.coverage_pct == 50.0

    def test_coverage_0_percent_all_untested(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("task1", prev_failed=1, curr_failed=1)
        tracker.record_task("task2", prev_failed=0, curr_failed=0)
        assert tracker.coverage_pct == 0.0

    def test_result_includes_failed_tests_count(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("task1", prev_failed=2, curr_failed=1)
        result = tracker.result(num_failed_tests=3)
        assert result.num_failed_tests == 3

    def test_result_not_tested_list_is_copy(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("task1", prev_failed=1, curr_failed=1)
        result = tracker.result(0)
        result.not_tested.clear()
        assert tracker._not_tested == ["task1"]

    def test_multiple_tasks_tracked_correctly(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("a", prev_failed=3, curr_failed=2)
        tracker.record_task("b", prev_failed=2, curr_failed=2)
        tracker.record_task("c", prev_failed=2, curr_failed=1)
        result = tracker.result(1)
        assert result.num_changed == 3
        assert result.num_tested == 2
        assert result.not_tested == ["b"]


class TestCoverageSkipBehavior:
    """
    coverage_skip tasks are excluded from tracking entirely.
    The callback handles the exclusion; these tests verify the tracker
    behaves correctly when coverage_skip tasks are simply never recorded.
    """

    def test_skipped_tasks_not_counted(self) -> None:
        tracker = CoverageTracker()
        tracker.record_task("real task", prev_failed=1, curr_failed=0)
        result = tracker.result(0)
        assert result.num_changed == 1
        assert "coverage_skip task" not in result.not_tested

    def test_all_skipped_means_zero_changed(self) -> None:
        tracker = CoverageTracker()
        result = tracker.result(0)
        assert result.num_changed == 0
        assert tracker.coverage_pct == 0.0
