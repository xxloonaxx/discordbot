"""Command line entrypoint for running the Discord bot."""

from __future__ import annotations

import asyncio

from bot.main import create_bot


def main() -> None:
    bot = create_bot()
    asyncio.run(bot.start(bot.config.discord.token))  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
