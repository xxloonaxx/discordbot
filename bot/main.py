"""Entrypoint utilities for constructing the Discord bot."""

from __future__ import annotations

import asyncio
import logging
from typing import Iterable

import discord
from discord.ext import commands

from . import config
from .cogs import general, moderation, music, nsfw, reactions, vrchat

_log = logging.getLogger(__name__)


def create_bot(bot_config: config.BotConfig | None = None) -> commands.Bot:
    """Instantiate the Discord bot with all cogs and configuration."""

    if bot_config is None:
        bot_config = config.BotConfig.from_env_or_file()

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(
        command_prefix=_create_prefix_function(bot_config.discord.default_prefix),
        intents=intents,
        description="Multifunctional community bot with VRChat and music support.",
    )

    _configure_logging()
    _load_cogs(bot, bot_config)

    @bot.event
    async def setup_hook() -> None:  # type: ignore[override]
        """Synchronise the slash command tree when the bot connects."""

        if bot_config.discord.guild_ids:
            for guild_id in bot_config.discord.guild_ids:
                guild = discord.Object(id=guild_id)
                await bot.tree.sync(guild=guild)
        else:
            await bot.tree.sync()

    @bot.event
    async def on_ready() -> None:  # type: ignore[override]
        assert bot.user is not None
        _log.info("Logged in as %s (%s)", bot.user.name, bot.user.id)
        await bot.change_presence(activity=discord.Game(name="Managing the community"))

    return bot


def run_bot() -> None:
    """Load configuration and run the bot."""

    bot = create_bot()
    asyncio.run(bot.start(bot.config.discord.token))  # type: ignore[attr-defined]


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )


def _load_cogs(bot: commands.Bot, bot_config: config.BotConfig) -> None:
    cog_factories: Iterable[tuple[str, commands.Cog]] = (
        ("General", general.GeneralCog(bot_config.discord)),
        ("Moderation", moderation.ModerationCog()),
        ("Music", music.MusicCog(bot_config.lavalink)),
        ("VRChat", vrchat.VRChatCog(bot_config.vrchat)),
        ("Reactions", reactions.ReactionCog(bot)),
        ("NSFW", nsfw.NSFWCog(bot)),
    )
    for name, cog in cog_factories:
        bot.add_cog(cog)
        _log.info("Loaded %s cog", name)

    bot.config = bot_config  # type: ignore[attr-defined]


def _create_prefix_function(default_prefix: str):
    async def dynamic_prefix(bot: commands.Bot, message: discord.Message):
        if not message.guild:
            return commands.when_mentioned_or(default_prefix)(bot, message)
        return commands.when_mentioned_or(default_prefix)(bot, message)

    return dynamic_prefix


__all__ = ["create_bot", "run_bot"]
