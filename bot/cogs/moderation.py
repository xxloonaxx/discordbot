"""Moderation utilities for managing a Discord community."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

import discord
from discord.ext import commands

from ..utils import embeds


@dataclass
class Infraction:
    user_id: int
    moderator_id: int
    reason: str
    action: str


class ModerationCog(commands.Cog):
    """Commands for server moderators."""

    def __init__(self) -> None:
        self._infractions: list[Infraction] = []

    async def _log_infraction(self, infraction: Infraction) -> None:
        self._infractions.append(infraction)

    def _require_permissions(self, ctx: commands.Context) -> None:
        if not ctx.author.guild_permissions.manage_guild:
            raise commands.CheckFailure("You do not have permission to run this command.")

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, limit: int = 10) -> None:
        deleted = await ctx.channel.purge(limit=limit + 1)
        await ctx.send(f"Deleted {len(deleted) - 1} messages.", delete_after=5)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> None:
        await member.kick(reason=reason)
        await ctx.send(f"{member} was kicked. Reason: {reason or 'No reason provided.'}")
        await self._log_infraction(
            Infraction(member.id, ctx.author.id, reason or "No reason provided", "kick"),
        )

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> None:
        await member.ban(reason=reason)
        await ctx.send(f"{member} was banned. Reason: {reason or 'No reason provided.'}")
        await self._log_infraction(
            Infraction(member.id, ctx.author.id, reason or "No reason provided", "ban"),
        )

    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(
        self,
        ctx: commands.Context,
        member: discord.Member,
        minutes: int,
        *,
        reason: Optional[str] = None,
    ) -> None:
        duration = discord.utils.utcnow() + timedelta(minutes=minutes)
        await member.edit(timeout=duration, reason=reason)
        await ctx.send(f"{member} has been timed out for {minutes} minutes.")
        await self._log_infraction(
            Infraction(member.id, ctx.author.id, reason or "No reason provided", "timeout"),
        )

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, delay: int) -> None:
        await ctx.channel.edit(slowmode_delay=delay)
        await ctx.send(f"Set slowmode to {delay} seconds.")

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> None:
        await self._log_infraction(
            Infraction(member.id, ctx.author.id, reason or "No reason provided", "warn"),
        )
        await ctx.send(f"{member.mention}, you have been warned. Reason: {reason or 'No reason provided.'}")

    @commands.command(name="infractions")
    @commands.has_permissions(manage_messages=True)
    async def infractions(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        member_id = member.id if member else ctx.author.id
        infractions = [inf for inf in self._infractions if inf.user_id == member_id]

        embed = embeds.default_embed(title="Infractions")
        if not infractions:
            embed.description = "No infractions found."
        else:
            for infraction in infractions:
                embed.add_field(
                    name=infraction.action.capitalize(),
                    value=f"Reason: {infraction.reason}\nModerator: <@{infraction.moderator_id}>",
                    inline=False,
                )
        await ctx.send(embed=embed)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: int, *, reason: Optional[str] = None) -> None:
        user = await ctx.bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(f"Unbanned {user}.")
        await self._log_infraction(
            Infraction(user.id, ctx.author.id, reason or "No reason provided", "unban"),
        )

    @commands.command(name="lockdown")
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx: commands.Context, *, reason: Optional[str] = None) -> None:
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=reason)
        await ctx.send("Channel is now in lockdown mode.")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context, *, reason: Optional[str] = None) -> None:
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=reason)
        await ctx.send("Channel has been unlocked.")

    @commands.command(name="remind")
    async def remind(self, ctx: commands.Context, minutes: int, *, message: str) -> None:
        await ctx.send(f"Reminder set for {minutes} minutes from now.")
        await asyncio.sleep(minutes * 60)
        await ctx.author.send(f"Reminder: {message}")


async def setup(bot: commands.Bot) -> None:
    bot.add_cog(ModerationCog())
