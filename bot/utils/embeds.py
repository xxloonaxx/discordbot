"""Helper utilities for building embeds consistently."""

from __future__ import annotations

from typing import Optional

import discord


DEFAULT_COLOUR = discord.Colour.blue()


def default_embed(*, title: Optional[str] = None, description: Optional[str] = None) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, colour=DEFAULT_COLOUR)
    embed.set_footer(text="Powered by discord.py")
    return embed
