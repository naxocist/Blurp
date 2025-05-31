from dotmap import DotMap

import discord
from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Bot
import asyncio

from utils.apis.jikanv4 import get_random_anime
from utils.apis.typhoon import get_synopsis_clue

# from credentials import guild_ids
from credentials import NAXOCIST_GUILD_ID


class AnimeClues(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    @commands.slash_command(
        guilds_ids=[NAXOCIST_GUILD_ID], description="guessing random anime!"
    )
    async def animeclues(self, ctx: ApplicationContext):
        await ctx.defer()
        anime = await get_random_anime()
        anime = anime.data

        synopsis_clue = await get_synopsis_clue(anime)

        await ctx.respond(synopsis_clue)


def setup(bot):
    bot.add_cog(AnimeClues(bot))
