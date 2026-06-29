from __future__ import annotations

from pathlib import Path

import pytest

from kirby.config import KirbyConfig, _mk_boolean, load_config

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestMkBoolean:
    def test_true_strings(self) -> None:
        for v in ("true", "True", "TRUE", "yes", "YES", "y", "Y", "1", "t", "T"):
            assert _mk_boolean(v) is True, f"expected True for {v!r}"

    def test_false_strings(self) -> None:
        for v in ("false", "False", "no", "n", "0", ""):
            assert _mk_boolean(v) is False, f"expected False for {v!r}"

    def test_none_returns_false(self) -> None:
        assert _mk_boolean(None) is False


class TestLoadConfig:
    def test_defaults_when_no_file(self) -> None:
        config = load_config(None)
        assert config == KirbyConfig(
            enable=False, serverspec_dir=None, serverspec_cmd=None
        )

    def test_from_config_file(self) -> None:
        config = load_config(FIXTURES / "kirby.cfg")
        assert config.enable is True
        assert config.serverspec_dir == "/opt"
        assert config.serverspec_cmd == "rake spec"

    def test_disabled_config_file(self) -> None:
        config = load_config(FIXTURES / "kirby_disabled.cfg")
        assert config.enable is False
        assert config.serverspec_dir == "/opt"

    def test_insufficient_config_file_uses_defaults_for_missing_keys(self) -> None:
        config = load_config(FIXTURES / "kirby_insufficient.cfg")
        assert config.enable is True
        assert config.serverspec_dir == "/opt"
        assert config.serverspec_cmd is None

    def test_nonexistent_file_falls_back_to_defaults(self) -> None:
        config = load_config(Path("/nonexistent/path/kirby.cfg"))
        assert config.enable is False
        assert config.serverspec_dir is None
        assert config.serverspec_cmd is None

    def test_empty_file_falls_back_to_defaults(self) -> None:
        config = load_config(FIXTURES / "empty.cfg")
        assert config.enable is False

    def test_env_vars_override_config_file(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("KIRBY_ENABLE", "no")
        monkeypatch.setenv("KIRBY_SERVERSPEC_DIR", "env_dir")
        monkeypatch.setenv("KIRBY_SERVERSPEC_CMD", "env_cmd")
        config = load_config(FIXTURES / "kirby.cfg")
        assert config.enable is False
        assert config.serverspec_dir == "env_dir"
        assert config.serverspec_cmd == "env_cmd"

    def test_env_vars_work_without_config_file(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("KIRBY_ENABLE", "yes")
        monkeypatch.setenv("KIRBY_SERVERSPEC_DIR", "/tmp")
        monkeypatch.setenv("KIRBY_SERVERSPEC_CMD", "rspec")
        config = load_config(None)
        assert config.enable is True
        assert config.serverspec_dir == "/tmp"
        assert config.serverspec_cmd == "rspec"

    def test_env_enable_overrides_file_enable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("KIRBY_ENABLE", "no")
        config = load_config(FIXTURES / "kirby.cfg")
        assert config.enable is False
        assert config.serverspec_dir == "/opt"
