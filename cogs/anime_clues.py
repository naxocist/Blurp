from dotmap import DotMap

import discord
from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Bot
import asyncio

from utils.apis.jikanv4 import get_random_anime
from utils.apis.typhoon import get_synopsis_clue

# from credentials import guild_ids
from credentials import NAXOCIST_GUILD_ID

guild_ids = [NAXOCIST_GUILD_ID]


class AnimeClues(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    clues = discord.SlashCommandGroup(
        "clues", "guess random anime based on clues", guild_ids=guild_ids
    )

    @clues.command(description="guessing random anime!")
    async def init(self, ctx: ApplicationContext):
        await ctx.defer()
        anime = await get_random_anime()
        anime = anime.data

        synopsis_clue = await get_synopsis_clue(anime)
        genres = " ".join(f"`{genre.name}`" for genre in anime.genres)

        await ctx.respond(
            embed=Embed(
                title="Anime Clues initialized!",
                description="You will be guessing a random anime as clues are gradually revealed...",
                color=Color.green(),
            )
        )

        timer = 180
        timer_msg = await ctx.send(
            embed=Embed(title=f"Time left: {timer} seconds", color=Color.dark_magenta())
        )

        await ctx.send(
            embed=Embed(title="Clue #1: Synopsis", description=synopsis_clue)
        )

        while timer > 0:
            await asyncio.sleep(1)
            timer -= 1

            if timer % 5 == 0 or timer <= 5:
                await timer_msg.edit(
                    embed=Embed(
                        title=f"Time left: {timer} seconds", color=Color.dark_magenta()
                    )
                )

            if timer == 170:
                await ctx.send(embed=Embed(title="Clue #2: Genres", description=genres))

    @clues.command(description="submit your guess!")
    async def answer(self, ctx: ApplicationContext):
        pass


def setup(bot):
    bot.add_cog(AnimeClues(bot))
