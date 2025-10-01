"""Reaction slash commands that respond with themed images."""

from __future__ import annotations

import logging
from typing import Final

import discord
from discord import app_commands
from discord.ext import commands

from ..utils import embeds, http

_log = logging.getLogger(__name__)


class ReactionCog(commands.Cog):
    """Provide fun reaction slash commands backed by nekos.best images."""

    API_BASE: Final[str] = "https://nekos.best/api/v2"
    REACTIONS: Final[dict[str, tuple[str, str]]] = {
        "cuddle": ("Cuddle", "kuschelt mit"),
        "hug": ("Hug", "umarmt"),
        "kiss": ("Kiss", "küsst"),
        "pat": ("Headpat", "streichelt den Kopf von"),
        "slap": ("Slap", "verpasst eine Schelle an"),
    }

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._http = http.JsonHttpClient(timeout=12.0)
        self._commands: list[app_commands.Command] = []
        for name in self.REACTIONS:
            command = self._build_command(name)
            self._commands.append(command)
            self.bot.tree.add_command(command)

    async def _fetch_reaction_image(self, endpoint: str) -> str | None:
        try:
            payload = await self._http.get(endpoint)
        except http.HTTPError as exc:
            _log.warning("Failed to fetch reaction image", exc_info=exc)
            return None
        results = payload.get("results")
        if isinstance(results, list) and results:
            url = results[0].get("url")
            if isinstance(url, str):
                return url
        _log.warning("Unexpected payload received from nekos.best: %s", payload)
        return None

    async def _send_reaction(
        self,
        interaction: discord.Interaction,
        category: str,
        member: discord.Member | None,
    ) -> None:
        base_url = f"{self.API_BASE}/{category}"
        image_url = await self._fetch_reaction_image(base_url)
        if image_url is None:
            await interaction.response.send_message(
                "Ich konnte gerade kein Bild laden. Bitte versuch es später erneut!",
                ephemeral=True,
            )
            return

        display_name, verb = self.REACTIONS[category]
        embed = embeds.default_embed(title=f"{display_name} Reaktion")
        embed.set_image(url=image_url)
        embed.set_footer(text="Bilder bereitgestellt von nekos.best")

        if member and member != interaction.user:
            description = f"{interaction.user.mention} {verb} {member.mention}!"
        elif member and member == interaction.user:
            description = f"{interaction.user.mention} {verb} sich selbst..."
        else:
            description = f"{interaction.user.mention} teilt ein {display_name} mit allen!"

        embed.description = description
        await interaction.response.send_message(embed=embed)

    def _build_command(self, name: str) -> app_commands.Command:
        display_name, _ = self.REACTIONS[name]
        description = f"Sende ein {display_name.lower()}-Bild als Reaktion."

        @app_commands.command(name=name, description=description)
        @app_commands.describe(member="Optionaler Nutzer, der in der Reaktion erwähnt werden soll")
        async def _command(interaction: discord.Interaction, member: discord.Member | None = None) -> None:
            await self._send_reaction(interaction, name, member)

        return _command

    async def cog_unload(self) -> None:
        await self._http.aclose()
        for command in self._commands:
            try:
                self.bot.tree.remove_command(command.name, type=command.type)
            except KeyError:
                continue


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionCog(bot))
