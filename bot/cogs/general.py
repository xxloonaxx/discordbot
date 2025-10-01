"""General utility commands for the bot."""

from __future__ import annotations

import platform
import time
from datetime import timedelta

import discord
from discord.ext import commands

from ..config import DiscordConfig
from ..utils import embeds


class GeneralCog(commands.Cog):
    """General commands available to all users."""

    def __init__(self, config: DiscordConfig) -> None:
        self.config = config
        self._start_time = time.perf_counter()

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Respond with the bot's latency."""

        latency = ctx.bot.latency * 1000
        await ctx.send(f"Pong! {latency:.2f}ms")

    @commands.command(name="about")
    async def about(self, ctx: commands.Context) -> None:
        """Display information about the bot."""

        embed = embeds.default_embed(
            title="About this bot",
            description="A multifunctional community assistant with VRChat and music features.",
        )
        embed.add_field(name="Prefix", value=self.config.default_prefix)
        embed.add_field(name="Python", value=platform.python_version())
        embed.add_field(name="discord.py", value=discord.__version__)
        embed.add_field(name="Uptime", value=self._uptime)
        await ctx.send(embed=embed)

    @property
    def _uptime(self) -> str:
        seconds = int(time.perf_counter() - self._start_time)
        return str(timedelta(seconds=seconds))


async def setup(bot: commands.Bot) -> None:
    bot.add_cog(GeneralCog(bot.config.discord))
