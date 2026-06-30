from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ServerspecResult:
    num_tests: int
    num_failed: int
    failed_tests: list[str] = field(default_factory=list)


class ServerspecRunner:
    """Run a Serverspec command and parse its output."""

    _num_tests_pattern = re.compile(r"(\d+) examples?, (\d+) failures?")
    _failed_tests_pattern = re.compile(r"^(rspec .*)$", re.MULTILINE)

    def __init__(self, serverspec_dir: str | None, serverspec_cmd: str | None) -> None:
        self.serverspec_dir = serverspec_dir
        self.serverspec_cmd = serverspec_cmd

    def run(self) -> ServerspecResult | None:
        if self.serverspec_dir is None:
            return None

        run_dir = Path(self.serverspec_dir)
        if not run_dir.is_dir():
            return None

        proc = subprocess.run(
            self.serverspec_cmd,
            shell=True,  # noqa: S602
            cwd=run_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = proc.stdout.decode("utf-8", errors="replace")

        # When using parallel_tests, the summary line appears multiple times.
        # Take the last match so we capture the aggregate totals.
        last_match = None
        for last_match in self._num_tests_pattern.finditer(output):
            pass
        if last_match is None:
            return None

        num_tests = int(last_match.group(1))
        num_failed = int(last_match.group(2))
        failed_tests = [m.group() for m in self._failed_tests_pattern.finditer(output)]

        return ServerspecResult(
            num_tests=num_tests,
            num_failed=num_failed,
            failed_tests=failed_tests,
        )
