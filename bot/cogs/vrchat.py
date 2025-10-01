"""VRChat group moderation commands."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from discord.ext import commands

from ..config import VRChatConfig
from ..utils import embeds


class VRChatError(RuntimeError):
    """Raised when the VRChat API returns an error response."""


@dataclass(slots=True)
class VRChatGroup:
    group_id: str
    name: str
    member_count: int


class VRChatClient:
    """Light-weight asynchronous client for interacting with the VRChat API."""

    BASE_URL = "https://api.vrchat.cloud/api/1"

    def __init__(self, config: VRChatConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient()
        self._authenticated = False

    async def ensure_authenticated(self) -> None:
        if self._authenticated:
            return
        auth = httpx.BasicAuth(self._config.username, self._config.password)
        params: Dict[str, Any] = {}
        if self._config.two_factor_code:
            params["code"] = self._config.two_factor_code
        response = await self._client.get(f"{self.BASE_URL}/auth/user", auth=auth, params=params)
        if response.status_code != 200:
            raise VRChatError(f"Authentication failed: {response.text}")
        self._authenticated = True

    async def get_groups(self) -> list[VRChatGroup]:
        await self.ensure_authenticated()
        response = await self._client.get(f"{self.BASE_URL}/groups")
        if response.status_code != 200:
            raise VRChatError(f"Failed to fetch groups: {response.text}")
        groups = []
        for item in response.json():
            groups.append(
                VRChatGroup(
                    group_id=item.get("id", "unknown"),
                    name=item.get("name", "Unnamed group"),
                    member_count=item.get("member_count", 0),
                )
            )
        return groups

    async def get_group(self, group_id: str) -> Dict[str, Any]:
        await self.ensure_authenticated()
        response = await self._client.get(f"{self.BASE_URL}/groups/{group_id}")
        if response.status_code != 200:
            raise VRChatError(f"Failed to fetch group: {response.text}")
        return response.json()

    async def promote_member(self, group_id: str, user_id: str, role_id: str) -> None:
        await self.ensure_authenticated()
        payload = {"userId": user_id, "roleId": role_id}
        response = await self._client.post(
            f"{self.BASE_URL}/groups/{group_id}/members/promote",
            json=payload,
        )
        if response.status_code != 200:
            raise VRChatError(f"Failed to promote member: {response.text}")

    async def demote_member(self, group_id: str, user_id: str, role_id: str) -> None:
        await self.ensure_authenticated()
        payload = {"userId": user_id, "roleId": role_id}
        response = await self._client.post(
            f"{self.BASE_URL}/groups/{group_id}/members/demote",
            json=payload,
        )
        if response.status_code != 200:
            raise VRChatError(f"Failed to demote member: {response.text}")

    async def invite_member(self, group_id: str, user_id: str) -> None:
        await self.ensure_authenticated()
        response = await self._client.post(
            f"{self.BASE_URL}/groups/{group_id}/invites",
            json={"userId": user_id},
        )
        if response.status_code != 200:
            raise VRChatError(f"Failed to invite member: {response.text}")

    async def close(self) -> None:
        await self._client.aclose()


class VRChatCog(commands.Cog):
    """Commands that integrate VRChat group management into Discord."""

    def __init__(self, config: Optional[VRChatConfig]) -> None:
        self.config = config
        self.client: Optional[VRChatClient] = VRChatClient(config) if config else None

    def cog_unload(self) -> None:
        if self.client:
            asyncio.create_task(self.client.close())

    def _ensure_client(self) -> VRChatClient:
        if not self.client:
            raise commands.CommandError("VRChat integration is not configured.")
        return self.client

    @commands.group(name="vrchat", invoke_without_command=True)
    async def vrchat(self, ctx: commands.Context) -> None:
        await ctx.send("Available subcommands: groups, groupinfo, invite, promote, demote")

    @vrchat.command(name="groups")
    async def groups(self, ctx: commands.Context) -> None:
        client = self._ensure_client()
        groups = await client.get_groups()
        embed = embeds.default_embed(title="VRChat Groups")
        if not groups:
            embed.description = "No groups found."
        else:
            for group in groups[:10]:
                embed.add_field(
                    name=group.name,
                    value=f"ID: {group.group_id}\nMembers: {group.member_count}",
                    inline=False,
                )
        await ctx.send(embed=embed)

    @vrchat.command(name="groupinfo")
    async def group_info(self, ctx: commands.Context, group_id: str) -> None:
        client = self._ensure_client()
        data = await client.get_group(group_id)
        embed = embeds.default_embed(title=data.get("name", "VRChat Group"))
        embed.add_field(name="ID", value=data.get("id", group_id))
        embed.add_field(name="Members", value=str(data.get("member_count", "unknown")))
        embed.add_field(name="Owner", value=data.get("ownerId", "unknown"))
        description = data.get("description")
        if description:
            embed.description = description[:2000]
        await ctx.send(embed=embed)

    @vrchat.command(name="invite")
    @commands.has_permissions(manage_guild=True)
    async def invite(self, ctx: commands.Context, group_id: str, user_id: str) -> None:
        client = self._ensure_client()
        await client.invite_member(group_id, user_id)
        await ctx.send(f"Invite sent to {user_id} for group {group_id}.")

    @vrchat.command(name="promote")
    @commands.has_permissions(manage_guild=True)
    async def promote(self, ctx: commands.Context, group_id: str, user_id: str, role_id: str) -> None:
        client = self._ensure_client()
        await client.promote_member(group_id, user_id, role_id)
        await ctx.send(f"Promoted {user_id} in group {group_id} to role {role_id}.")

    @vrchat.command(name="demote")
    @commands.has_permissions(manage_guild=True)
    async def demote(self, ctx: commands.Context, group_id: str, user_id: str, role_id: str) -> None:
        client = self._ensure_client()
        await client.demote_member(group_id, user_id, role_id)
        await ctx.send(f"Demoted {user_id} in group {group_id} from role {role_id}.")


async def setup(bot: commands.Bot) -> None:
    bot.add_cog(VRChatCog(bot.config.vrchat))
