from __future__ import annotations
from core import Bot
from .. import Plugin

import discord
from discord.ext import commands
from discord.ext.commands.context import Context

import asyncio
import random

import requests

class Commands(Plugin):
    def __init__(self, bot: Bot):
        self.bot = bot
    

    @commands.command()
    async def action(self, ctx, who: str, tag: str):

        res = requests.get("https://nekos.best/api/v2/" + tag)
        data = res.json()
        # print(data["results"][0]["url"])

        incident = f"{ctx.author.mention} {tag} {who}"
        gif = data["results"][0]["url"]


        embed = discord.Embed(color=discord.Colour.random(), type="image")
        embed.set_image(url=gif)
        await ctx.send(incident)
        await ctx.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Commands(bot))