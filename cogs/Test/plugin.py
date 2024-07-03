from __future__ import annotations
from core import Bot
from .. import Plugin

import discord
from discord.ext import commands
from discord import app_commands


class TestCog(Plugin):
    def __init__(self, bot: Bot):
        self.bot = bot
    
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong!")
    

    @commands.command()
    async def embed(self, ctx):

        embed = discord.Embed()

        embed.title = 'This is title'
        embed.description = 'This is description'
        embed.colour = discord.Colour.blue()

        file = discord.File('./assets/profile.jpeg', filename="profile.jpeg")
        embed.set_image(url='attachment://profile.jpeg')
        embed.set_thumbnail(url='attachment://profile.jpeg')
        embed.set_footer(text='This is foother', icon_url=ctx.author.avatar.url)
        embed.set_author(name=ctx.author.nick, url='https://www.google.co.th/', icon_url=ctx.author.avatar.url)

        embed.add_field(name='this is name', value='this is value', inline=True)
        embed.add_field(name='this is name', value='this is value', inline=True)

        await ctx.send(file=file, embed=embed)
    

async def setup(bot: Bot):
    await bot.add_cog(TestCog(bot))