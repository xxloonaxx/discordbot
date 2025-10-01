"""Configuration utilities for the Discord bot."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


CONFIG_FILENAMES = ("botconfig.json", "config.json")


@dataclass(slots=True)
class DiscordConfig:
    """Discord related configuration values."""

    token: str
    guild_ids: tuple[int, ...]
    default_prefix: str = "!"


@dataclass(slots=True)
class VRChatConfig:
    """Configuration required to interact with the VRChat API."""

    username: str
    password: str
    two_factor_code: Optional[str] = None


@dataclass(slots=True)
class LavalinkConfig:
    """Configuration for connecting to a Lavalink node for music playback."""

    host: str = "localhost"
    port: int = 2333
    password: str = "youshallnotpass"
    https: bool = False


@dataclass(slots=True)
class BotConfig:
    """Top-level configuration container."""

    discord: DiscordConfig
    vrchat: Optional[VRChatConfig] = None
    lavalink: Optional[LavalinkConfig] = None

    @classmethod
    def from_env_or_file(cls) -> "BotConfig":
        """Build a configuration object from environment variables or json files."""

        config = _load_from_file()
        if config:
            return cls(**config)

        return cls(
            discord=DiscordConfig(
                token=_require_env("DISCORD_TOKEN"),
                guild_ids=_parse_ids(os.getenv("DISCORD_GUILD_IDS", "")),
                default_prefix=os.getenv("DISCORD_PREFIX", "!"),
            ),
            vrchat=_load_vrchat_from_env(),
            lavalink=_load_lavalink_from_env(),
        )


def _load_from_file() -> Optional[Dict[str, Any]]:
    for filename in CONFIG_FILENAMES:
        path = Path(filename)
        if path.exists():
            with path.open("r", encoding="utf8") as handle:
                return json.load(handle)
    return None


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing environment variable: {key}")
    return value


def _parse_ids(raw: str) -> tuple[int, ...]:
    ids = []
    for bit in raw.split(","):
        bit = bit.strip()
        if bit:
            ids.append(int(bit))
    return tuple(ids)


def _load_vrchat_from_env() -> Optional[VRChatConfig]:
    username = os.getenv("VRCHAT_USERNAME")
    password = os.getenv("VRCHAT_PASSWORD")
    if not username or not password:
        return None
    return VRChatConfig(
        username=username,
        password=password,
        two_factor_code=os.getenv("VRCHAT_2FA_CODE"),
    )


def _load_lavalink_from_env() -> Optional[LavalinkConfig]:
    host = os.getenv("LAVALINK_HOST")
    password = os.getenv("LAVALINK_PASSWORD")
    if not host and not password:
        return None
    return LavalinkConfig(
        host=host or LavalinkConfig.host,
        port=int(os.getenv("LAVALINK_PORT", LavalinkConfig.port)),
        password=password or LavalinkConfig.password,
        https=os.getenv("LAVALINK_USE_HTTPS", "false").lower() in {"true", "1", "yes"},
    )
