from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class KirbyConfig:
    enable: bool
    serverspec_dir: str | None
    serverspec_cmd: str | None


def _mk_boolean(value: str | None) -> bool:
    if value is None:
        return False
    return str(value).lower() in ("true", "t", "y", "1", "yes")


def _get_config(
    parser: configparser.ConfigParser,
    section: str,
    option: str,
    env_var: str,
    default: str | None,
) -> str | None:
    env_value = os.environ.get(env_var)
    if env_value is not None:
        return env_value
    try:
        return parser.get(section, option)
    except (configparser.NoOptionError, configparser.NoSectionError):
        return default


def load_config(config_file: Path | None) -> KirbyConfig:
    parser = configparser.ConfigParser()
    if config_file is not None:
        parser.read(config_file)

    enable = _mk_boolean(
        _get_config(parser, "defaults", "enable", "KIRBY_ENABLE", "false")
    )
    serverspec_dir = _get_config(
        parser, "defaults", "serverspec_dir", "KIRBY_SERVERSPEC_DIR", None
    )
    serverspec_cmd = _get_config(
        parser, "defaults", "serverspec_cmd", "KIRBY_SERVERSPEC_CMD", None
    )

    return KirbyConfig(
        enable=enable,
        serverspec_dir=serverspec_dir,
        serverspec_cmd=serverspec_cmd,
    )
