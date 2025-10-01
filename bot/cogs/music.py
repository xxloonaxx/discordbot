"""Music playback commands leveraging Lavalink via wavelink."""

from __future__ import annotations

import logging
from typing import Optional

from discord.ext import commands
import wavelink

from ..config import LavalinkConfig

_log = logging.getLogger(__name__)


class MusicCog(commands.Cog):
    """Music commands for the Discord bot."""

    def __init__(self, config: Optional[LavalinkConfig]) -> None:
        self.config = config or LavalinkConfig()
        self._node: Optional[wavelink.Node] = None

    async def cog_load(self) -> None:
        if not wavelink.NodePool.nodes:
            await self._connect_node()

    async def _connect_node(self) -> None:
        if not hasattr(self, "bot"):
            raise RuntimeError("Cog is not attached to a bot yet.")
        _log.info(
            "Connecting to Lavalink node at %s:%s (https=%s)",
            self.config.host,
            self.config.port,
            self.config.https,
        )
        self._node = await wavelink.NodePool.create_node(
            bot=self.bot,
            host=self.config.host,
            port=self.config.port,
            password=self.config.password,
            https=self.config.https,
        )

    async def ensure_voice(self, ctx: commands.Context) -> wavelink.Player:
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You must be in a voice channel to use this command.")

        player: Optional[wavelink.Player] = ctx.voice_client  # type: ignore[assignment]
        if not player:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        elif ctx.author.voice.channel != player.channel:
            await player.move_to(ctx.author.voice.channel)
        return player

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, search: str) -> None:
        player = await self.ensure_voice(ctx)
        track = await wavelink.YouTubeTrack.search(search, return_first=True)
        if not track:
            await ctx.send("No results found.")
            return
        await player.play(track)
        await ctx.send(f"Now playing: {track.title}")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> None:
        player = await self.ensure_voice(ctx)
        await player.pause()
        await ctx.send("Playback paused.")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> None:
        player = await self.ensure_voice(ctx)
        await player.resume()
        await ctx.send("Playback resumed.")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context) -> None:
        player = await self.ensure_voice(ctx)
        await player.stop()
        await ctx.send("Playback stopped.")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context) -> None:
        player = await self.ensure_voice(ctx)
        await player.stop()
        await ctx.send("Skipped the current track.")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context) -> None:
        player = ctx.voice_client
        if player:
            await player.disconnect()
            await ctx.send("Disconnected from the voice channel.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicCog(bot.config.lavalink))
