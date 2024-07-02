from __future__ import annotations
import os

from typing import Optional
from discord.ext import commands
from logging import getLogger; log = getLogger("Bot")
import discord

__all__ = (
    "Bot",
)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=".",
            intents=discord.Intents.all(),
        )

        self.activity = discord.Activity(name='for commands', type=discord.ActivityType.watching)
    

    async def setup_hook(self) -> None:
        for file in os.listdir('cogs'):
            if not file.startswith('_'):
                await self.load_extension(f"cogs.{file}.plugin")
    

    async def on_ready(self) -> None:
        log.info(f"logged in as {self.user}")
    

    async def success(self, content: str, Interaction: discord.Interaction, ephemeral: Optional[bool]):
        pass


    async def error(self, content: str, Interaction: discord.Interaction, ephemeral: Optional[bool]):
        pass

