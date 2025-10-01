"""Slash commands that provide NSFW media backed by a public API."""

from __future__ import annotations

import logging
from typing import Final

import discord
from discord import app_commands
from discord.ext import commands

from ..utils import embeds, http

_log = logging.getLogger(__name__)


class NSFWCog(commands.Cog):
    """Provide NSFW imagery from nekobot.xyz via slash commands."""

    API_URL: Final[str] = "https://nekobot.xyz/api/image"
    CATEGORIES: Final[dict[str, str]] = {
        "hentai": "Hentai",
        "boobs": "Boobs",
        "ass": "Ass",
        "thigh": "Thigh",
    }

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._http = http.JsonHttpClient(timeout=12.0)

    async def cog_unload(self) -> None:
        await self._http.aclose()

    async def _fetch_image(self, category: str) -> str | None:
        try:
            payload = await self._http.get(self.API_URL, params={"type": category})
        except http.HTTPError as exc:
            _log.warning("Failed to retrieve NSFW image", exc_info=exc)
            return None
        if payload.get("success") and isinstance(payload.get("message"), str):
            return str(payload["message"])
        _log.warning("Unexpected payload from nekobot.xyz: %s", payload)
        return None

    @staticmethod
    def _ensure_nsfw_channel(interaction: discord.Interaction) -> bool:
        channel = interaction.channel
        if channel is None:
            return False

        is_nsfw = getattr(channel, "is_nsfw", None)
        if callable(is_nsfw):
            try:
                if is_nsfw():
                    return True
            except Exception:  # pragma: no cover - defensive, API dependent
                pass

        parent = getattr(channel, "parent", None)
        if parent is not None:
            parent_is_nsfw = getattr(parent, "is_nsfw", None)
            if callable(parent_is_nsfw):
                try:
                    return bool(parent_is_nsfw())
                except Exception:  # pragma: no cover - defensive, API dependent
                    return False

        return False

    @app_commands.command(name="nsfw", description="Hole ein zufälliges NSFW-Bild aus einer Kategorie.")
    @app_commands.describe(category="Kategorie des Bildes")
    @app_commands.choices(
        category=[
            app_commands.Choice(name=display, value=key)
            for key, display in CATEGORIES.items()
        ]
    )
    async def nsfw(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
    ) -> None:
        if not self._ensure_nsfw_channel(interaction):
            await interaction.response.send_message(
                "Dieser Befehl kann nur in als NSFW markierten Kanälen benutzt werden.",
                ephemeral=True,
            )
            return

        image_url = await self._fetch_image(category.value)
        if image_url is None:
            await interaction.response.send_message(
                "Aktuell konnte kein Bild geladen werden. Bitte versuch es später erneut!",
                ephemeral=True,
            )
            return

        embed = embeds.default_embed(title=f"{category.name} Bild")
        embed.set_image(url=image_url)
        embed.set_footer(text="Bilder bereitgestellt von nekobot.xyz")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NSFWCog(bot))
