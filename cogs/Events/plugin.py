from __future__ import annotations
from core import Bot
from .. import Plugin

import discord
from discord.ext import commands


class Events(Plugin):
    def __init__(self, bot: Bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print(self.bot.user, " is ready!")


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
            
        if isinstance(error, commands.MissingPermissions):
            permission_warn = "You're not allowed to do that!"
            await ctx.send(embed=discord.Embed(title=permission_warn, color=discord.Colour.red()))

        elif isinstance(error, commands.errors.CommandOnCooldown):
            cooldown_warn = f"`Cooling down! try again in {int(error.retry_after)}s.`"
            await ctx.send(cooldown_warn)
            
        else:
            raise error.original


async def setup(bot: Bot):
    await bot.add_cog(Events(bot))