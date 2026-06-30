"""
Pytest configuration: injects the ansible_collections namespace and mocks
Ansible imports so unit tests run without ansible-core or an installed collection.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Build the ansible_collections.stefanfluit.kirby namespace so tests can
# import from it without installing the collection.
_NS = [
    "ansible_collections",
    "ansible_collections.stefanfluit",
    "ansible_collections.stefanfluit.kirby",
    "ansible_collections.stefanfluit.kirby.plugins",
    "ansible_collections.stefanfluit.kirby.plugins.callback",
    "ansible_collections.stefanfluit.kirby.plugins.module_utils",
]
for _dotted in _NS:
    if _dotted not in sys.modules:
        _mod = types.ModuleType(_dotted)
        _mod.__path__ = []
        _mod.__package__ = _dotted
        sys.modules[_dotted] = _mod

sys.modules["ansible_collections.stefanfluit.kirby.plugins.callback"].__path__ = [
    str(PROJECT_ROOT / "plugins" / "callback")
]
sys.modules["ansible_collections.stefanfluit.kirby.plugins.module_utils"].__path__ = [
    str(PROJECT_ROOT / "plugins" / "module_utils")
]

# Keep project root on sys.path for any direct file-based imports.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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
