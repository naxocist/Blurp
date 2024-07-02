from __future__ import annotations
from core import Bot
from .. import Plugin

import discord
from discord.ext import commands
from discord.ext.commands.context import Context

import asyncio
import random


class Commands(Plugin):
    def __init__(self, bot: Bot):
        self.bot = bot
    

    @commands.command()
    async def pt(ctx, tag) -> None:
        if not isinstance(tag, discord.Member.mention):
            await ctx.send("Please tag someone!")
    
        print(type(tag))
        await ctx.send(tag)


async def setup(bot: Bot):
    await bot.add_cog(Commands(bot))