"""
Pytest configuration: extends sys.path and mocks Ansible imports so unit tests
run without ansible-core installed.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Ensure the project root is on sys.path (for callback_plugins imports).
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure src/ is on sys.path so kirby package is importable without pip install.
_src = str(PROJECT_ROOT / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)


class _FakeCallbackBase:
    """Minimal stand-in for ansible.plugins.callback.CallbackBase."""

    def __init__(self) -> None:
        self._display = MagicMock()
        super().__init__()


def _install_ansible_mocks() -> None:
    if "ansible" in sys.modules:
        return

    ansible_mod = types.ModuleType("ansible")
    plugins_mod = types.ModuleType("ansible.plugins")
    callback_mod = types.ModuleType("ansible.plugins.callback")
    utils_mod = types.ModuleType("ansible.utils")
    display_mod = types.ModuleType("ansible.utils.display")

    callback_mod.CallbackBase = _FakeCallbackBase  # type: ignore[attr-defined]
    display_mod.Display = MagicMock  # type: ignore[attr-defined]

    ansible_mod.plugins = plugins_mod  # type: ignore[attr-defined]
    ansible_mod.utils = utils_mod  # type: ignore[attr-defined]
    plugins_mod.callback = callback_mod  # type: ignore[attr-defined]
    utils_mod.display = display_mod  # type: ignore[attr-defined]

    sys.modules["ansible"] = ansible_mod
    sys.modules["ansible.plugins"] = plugins_mod
    sys.modules["ansible.plugins.callback"] = callback_mod
    sys.modules["ansible.utils"] = utils_mod
    sys.modules["ansible.utils.display"] = display_mod


_install_ansible_mocks()
