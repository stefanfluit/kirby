"""Ansible callback plugin that measures Serverspec coverage of changed tasks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ansible.plugins.callback import CallbackBase
from ansible.utils.display import Display

from kirby.config import KirbyConfig, load_config
from kirby.coverage import CoverageTracker
from kirby.runner import ServerspecResult, ServerspecRunner

CALLBACK_VERSION = 2.0
CALLBACK_TYPE = "notification"
CALLBACK_NAME = "kirby"
CALLBACK_NEEDS_ENABLED = False

display = Display()


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "kirby"
    CALLBACK_NEEDS_ENABLED = False

    def __init__(self) -> None:
        super().__init__()

        config_env = os.environ.get("KIRBY_CONFIG")
        config_file: Path | None = (
            Path(config_env) if config_env else Path.cwd() / "kirby.cfg"
        )

        self._config: KirbyConfig = load_config(config_file)
        self._kirby_enabled: bool = self._config.enable

        if self._kirby_enabled and not self._validate_config():
            self._kirby_enabled = False

        if self._kirby_enabled:
            self._runner = ServerspecRunner(
                self._config.serverspec_dir,
                self._config.serverspec_cmd,
            )
            self._tracker = CoverageTracker()
            self._curr_task_name: str = ""
            self._num_tests: int = 0
            self._num_failed_tests: int = 0
            self._failed_tests: list[str] = []
            self._dirty: bool = False

    def _validate_config(self) -> bool:
        if not self._config.serverspec_dir:
            display.display("[kirby] 'serverspec_dir' is not correctly defined")
            return False
        if not self._config.serverspec_cmd:
            display.display("[kirby] 'serverspec_cmd' is not correctly defined")
            return False
        return True

    def v2_playbook_on_start(self, playbook: Any) -> None:
        if not self._kirby_enabled:
            return

        result = self._runner.run()
        if result is None:
            display.display("[kirby] serverspec settings invalid, disabling kirby")
            self._kirby_enabled = False
            return

        self._apply_result(result)
        self._dirty = False

    def v2_playbook_on_task_start(self, task: Any, is_conditional: bool) -> None:
        if not self._kirby_enabled:
            return

        self._curr_task_name = (
            task.get_name() if hasattr(task, "get_name") else str(task)
        )

        if self._dirty and "coverage_skip" not in self._curr_task_name:
            self._sync()

    def v2_runner_on_ok(self, result: Any) -> None:
        if not self._kirby_enabled:
            return

        res_dict: dict[str, Any] = getattr(result, "_result", {})
        if not res_dict.get("changed", False):
            return

        if "coverage_skip" in self._curr_task_name:
            self._dirty = True
            return

        new_result = self._runner.run()
        if new_result is None:
            return

        prev_failed = self._num_failed_tests
        prev_failed_tests = self._failed_tests

        self._apply_result(new_result)

        newly_passing = set(prev_failed_tests) - set(self._failed_tests)
        display.display("tested by:", color="yellow")
        for test in newly_passing:
            display.display(f"- {test}", color="yellow")

        self._tracker.record_task(
            self._curr_task_name,
            prev_failed=prev_failed,
            curr_failed=self._num_failed_tests,
        )

    def v2_playbook_on_stats(self, stats: Any) -> None:
        if not self._kirby_enabled:
            return

        if self._dirty:
            self._sync()

        cov = self._tracker.result(self._num_failed_tests)

        display.display("*** Kirby Results ***")
        display.display(
            f"Coverage  : {self._tracker.coverage_pct:.0f}%"
            f" ({cov.num_tested} of {cov.num_changed} tasks are tested)"
        )

        if cov.not_tested:
            display.display("Not tested:")
            for task in cov.not_tested:
                display.display(f" - {task}")

        if cov.num_failed_tests > 0:
            display.display("")
            display.display(
                f"WARNING: serverspec still detects {cov.num_failed_tests} failures"
            )

        display.display("*** Kirby End *******")

    def _sync(self) -> None:
        result = self._runner.run()
        if result is None:
            return
        self._apply_result(result)
        self._dirty = False

    def _apply_result(self, result: ServerspecResult) -> None:
        self._num_tests = result.num_tests
        self._num_failed_tests = result.num_failed
        self._failed_tests = result.failed_tests
