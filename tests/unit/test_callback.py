"""
Focused unit tests for the Ansible callback adapter.

Ansible is mocked via conftest.py, so these tests run without ansible-core.
The logic for config/runner/coverage is tested separately; here we verify
the callback wires them together correctly, including coverage_skip handling.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from kirby.runner import ServerspecResult

FIXTURES = Path(__file__).parent.parent / "fixtures"


class _FakeTask:
    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name


class _FakeResult:
    def __init__(self, changed: bool = False) -> None:
        self._result = {"changed": changed}


def _make_callback(cfg_path: Path) -> object:
    """Instantiate CallbackModule with a given config file."""
    if "callback_plugins.kirby" in sys.modules:
        del sys.modules["callback_plugins.kirby"]

    os.environ["KIRBY_CONFIG"] = str(cfg_path)
    try:
        from callback_plugins.kirby import CallbackModule

        return CallbackModule()
    finally:
        del os.environ["KIRBY_CONFIG"]


class TestCallbackInit:
    def test_enabled_with_valid_config(self) -> None:
        cb = _make_callback(FIXTURES / "kirby.cfg")
        assert cb._kirby_enabled is True  # type: ignore[attr-defined]

    def test_disabled_config_file_disables_kirby(self) -> None:
        cb = _make_callback(FIXTURES / "kirby_disabled.cfg")
        assert cb._kirby_enabled is False  # type: ignore[attr-defined]

    def test_missing_serverspec_cmd_disables_kirby(self) -> None:
        cb = _make_callback(FIXTURES / "kirby_insufficient.cfg")
        assert cb._kirby_enabled is False  # type: ignore[attr-defined]

    def test_empty_config_disables_kirby(self) -> None:
        cb = _make_callback(FIXTURES / "empty.cfg")
        assert cb._kirby_enabled is False  # type: ignore[attr-defined]


class TestCallbackPlaybookOnStart:
    def test_invalid_runner_result_disables_kirby(self) -> None:
        cb = _make_callback(FIXTURES / "kirby.cfg")
        with patch.object(cb._runner, "run", return_value=None):  # type: ignore[attr-defined]
            cb.v2_playbook_on_start(MagicMock())  # type: ignore[attr-defined]
        assert cb._kirby_enabled is False  # type: ignore[attr-defined]

    def test_valid_runner_result_keeps_kirby_enabled(self) -> None:
        cb = _make_callback(FIXTURES / "kirby.cfg")
        result = ServerspecResult(num_tests=2, num_failed=1, failed_tests=["rspec a"])
        with patch.object(cb._runner, "run", return_value=result):  # type: ignore[attr-defined]
            cb.v2_playbook_on_start(MagicMock())  # type: ignore[attr-defined]
        assert cb._kirby_enabled is True  # type: ignore[attr-defined]
        assert cb._num_failed_tests == 1  # type: ignore[attr-defined]


class TestCallbackCoverageSkip:
    def _setup(self) -> object:
        cb = _make_callback(FIXTURES / "kirby.cfg")
        cb._num_tests = 2  # type: ignore[attr-defined]
        cb._num_failed_tests = 2  # type: ignore[attr-defined]
        cb._failed_tests = []  # type: ignore[attr-defined]
        cb._dirty = False  # type: ignore[attr-defined]
        return cb

    def test_coverage_skip_task_sets_dirty_flag(self) -> None:
        cb = self._setup()
        cb.v2_playbook_on_task_start(  # type: ignore[attr-defined]
            _FakeTask("deploy thing [coverage_skip]"), False
        )
        cb.v2_runner_on_ok(_FakeResult(changed=True))  # type: ignore[attr-defined]
        assert cb._dirty is True  # type: ignore[attr-defined]

    def test_coverage_skip_task_not_counted_in_tracker(self) -> None:
        cb = self._setup()
        cb.v2_playbook_on_task_start(  # type: ignore[attr-defined]
            _FakeTask("deploy thing [coverage_skip]"), False
        )
        cb.v2_runner_on_ok(_FakeResult(changed=True))  # type: ignore[attr-defined]
        assert cb._tracker._num_changed == 0  # type: ignore[attr-defined]

    def test_dirty_flag_cleared_on_next_non_skip_task(self) -> None:
        cb = self._setup()
        cb._dirty = True  # type: ignore[attr-defined]
        sync_result = ServerspecResult(num_tests=2, num_failed=1, failed_tests=[])
        with patch.object(cb._runner, "run", return_value=sync_result):  # type: ignore[attr-defined]
            cb.v2_playbook_on_task_start(  # type: ignore[attr-defined]
                _FakeTask("regular task"), False
            )
        assert cb._dirty is False  # type: ignore[attr-defined]
        assert cb._num_failed_tests == 1  # type: ignore[attr-defined]

    def test_dirty_flag_not_cleared_on_another_skip_task(self) -> None:
        cb = self._setup()
        cb._dirty = True  # type: ignore[attr-defined]
        cb.v2_playbook_on_task_start(  # type: ignore[attr-defined]
            _FakeTask("also [coverage_skip]"), False
        )
        assert cb._dirty is True  # type: ignore[attr-defined]


class TestCallbackRunnerOnOk:
    def _setup_with_initial_result(self, num_failed: int, failed: list[str]) -> object:
        cb = _make_callback(FIXTURES / "kirby.cfg")
        cb._num_tests = 2  # type: ignore[attr-defined]
        cb._num_failed_tests = num_failed  # type: ignore[attr-defined]
        cb._failed_tests = failed  # type: ignore[attr-defined]
        cb._dirty = False  # type: ignore[attr-defined]
        cb._curr_task_name = "my task"  # type: ignore[attr-defined]
        return cb

    def test_unchanged_result_skipped(self) -> None:
        cb = self._setup_with_initial_result(1, [])
        with patch.object(cb._runner, "run") as mock_run:  # type: ignore[attr-defined]
            cb.v2_runner_on_ok(_FakeResult(changed=False))  # type: ignore[attr-defined]
            mock_run.assert_not_called()

    def test_changed_and_tested_increments_tested(self) -> None:
        cb = self._setup_with_initial_result(2, ["rspec a", "rspec b"])
        after = ServerspecResult(num_tests=2, num_failed=1, failed_tests=["rspec b"])
        with patch.object(cb._runner, "run", return_value=after):  # type: ignore[attr-defined]
            cb.v2_runner_on_ok(_FakeResult(changed=True))  # type: ignore[attr-defined]
        assert cb._tracker._num_tested == 1  # type: ignore[attr-defined]
        assert cb._tracker._not_tested == []  # type: ignore[attr-defined]

    def test_changed_but_untested_adds_to_not_tested(self) -> None:
        cb = self._setup_with_initial_result(1, ["rspec a"])
        after = ServerspecResult(num_tests=2, num_failed=1, failed_tests=["rspec a"])
        with patch.object(cb._runner, "run", return_value=after):  # type: ignore[attr-defined]
            cb.v2_runner_on_ok(_FakeResult(changed=True))  # type: ignore[attr-defined]
        assert cb._tracker._not_tested == ["my task"]  # type: ignore[attr-defined]


class TestCallbackPlaybookOnStats:
    def test_stats_runs_sync_if_dirty(self) -> None:
        cb = _make_callback(FIXTURES / "kirby.cfg")
        cb._dirty = True  # type: ignore[attr-defined]
        cb._num_failed_tests = 0  # type: ignore[attr-defined]
        cb._failed_tests = []  # type: ignore[attr-defined]
        sync_result = ServerspecResult(num_tests=1, num_failed=0, failed_tests=[])
        with patch.object(cb._runner, "run", return_value=sync_result):  # type: ignore[attr-defined]
            cb.v2_playbook_on_stats(MagicMock())  # type: ignore[attr-defined]
        assert cb._dirty is False  # type: ignore[attr-defined]

    def test_disabled_callback_does_nothing(self) -> None:
        cb = _make_callback(FIXTURES / "empty.cfg")
        cb.v2_playbook_on_stats(MagicMock())  # type: ignore[attr-defined]
