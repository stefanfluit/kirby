from __future__ import annotations

from unittest.mock import MagicMock, patch

from ansible_collections.stefanfluit.kirby.plugins.module_utils.runner import (
    ServerspecResult,
    ServerspecRunner,
)


def _make_runner(directory: str = ".") -> ServerspecRunner:
    return ServerspecRunner(directory, "rake spec")


def _mock_proc(stdout: bytes, returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.stdout = stdout
    proc.returncode = returncode
    return proc


class TestServerspecRunnerRun:
    def test_no_failures(self) -> None:
        with patch("subprocess.run", return_value=_mock_proc(b"1 example, 0 failures")):
            result = _make_runner().run()
        assert result == ServerspecResult(num_tests=1, num_failed=0, failed_tests=[])

    def test_one_failure(self) -> None:
        output = b"1 example, 1 failure\nrspec ./spec/localhost/sample_spec.rb:4"
        with patch("subprocess.run", return_value=_mock_proc(output, 1)):
            result = _make_runner().run()
        assert result is not None
        assert result.num_tests == 1
        assert result.num_failed == 1
        assert result.failed_tests == ["rspec ./spec/localhost/sample_spec.rb:4"]

    def test_two_failures(self) -> None:
        output = b"2 examples, 2 failures\nrspec a\nrspec b"
        with patch("subprocess.run", return_value=_mock_proc(output, 1)):
            result = _make_runner().run()
        assert result is not None
        assert result.num_tests == 2
        assert result.num_failed == 2
        assert result.failed_tests == ["rspec a", "rspec b"]

    def test_plural_example_and_failure(self) -> None:
        output = b"3 examples, 0 failures"
        with patch("subprocess.run", return_value=_mock_proc(output)):
            result = _make_runner().run()
        assert result is not None
        assert result.num_tests == 3
        assert result.num_failed == 0

    def test_large_numbers(self) -> None:
        with patch(
            "subprocess.run",
            return_value=_mock_proc(b"100 examples, 99 failures", 1),
        ):
            result = _make_runner().run()
        assert result is not None
        assert result.num_tests == 100
        assert result.num_failed == 99

    def test_parallel_output_uses_last_match(self) -> None:
        output = (
            b"1 example, 0 failures\n2 examples, 0 failures\n3 examples, 0 failures"
        )
        with patch("subprocess.run", return_value=_mock_proc(output)):
            result = _make_runner().run()
        assert result is not None
        assert result.num_tests == 3

    def test_parallel_with_failures_uses_last_match(self) -> None:
        output = (
            b"1 example, 1 failure\nrspec a\n"
            b"1 example, 1 failure\nrspec b\n"
            b"2 examples, 2 failures"
        )
        with patch("subprocess.run", return_value=_mock_proc(output, 1)):
            result = _make_runner().run()
        assert result is not None
        assert result.num_tests == 2
        assert result.num_failed == 2
        assert result.failed_tests == ["rspec a", "rspec b"]

    def test_invalid_output_returns_none(self) -> None:
        with patch("subprocess.run", return_value=_mock_proc(b"")):
            result = _make_runner().run()
        assert result is None

    def test_unrecognised_output_returns_none(self) -> None:
        with patch("subprocess.run", return_value=_mock_proc(b"no match here")):
            result = _make_runner().run()
        assert result is None

    def test_none_dir_returns_none(self) -> None:
        runner = ServerspecRunner(None, "rake spec")
        assert runner.run() is None

    def test_nonexistent_dir_returns_none(self) -> None:
        runner = ServerspecRunner("/nonexistent-kirby-test-dir", "rake spec")
        assert runner.run() is None

    def test_failed_subprocess_output_still_parsed(self) -> None:
        output = b"1 example, 1 failure\nrspec ./spec/fail_spec.rb:10"
        with patch("subprocess.run", return_value=_mock_proc(output, returncode=1)):
            result = _make_runner().run()
        assert result is not None
        assert result.num_failed == 1
        assert len(result.failed_tests) == 1
