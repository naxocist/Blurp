import discord
from discord.ext import commands
from discord import ApplicationContext, Embed, Color, Bot

import asyncio
from typing import List
from random import randint
from pprint import pprint

from utils.apis.jikanv4 import get_anime_by_id
from utils.apis.typhoon import get_synopsis_clue
from utils.apis.MAL import get_user_anime_list

# from credentials import guild_ids
from credentials import NAXOCIST_GUILD_ID

guild_ids = [NAXOCIST_GUILD_ID]


class AniClues(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    clues = discord.SlashCommandGroup(
        "clues", "Guessing random anime minigame based on clues", guild_ids=guild_ids
    )

    @clues.command(description="start guessing random anime from your MAL profile!")
    async def init(self, ctx: ApplicationContext, mal_username):
        await ctx.respond(
            embed=Embed(
                title="Anime Clues initialized!",
                description="You will be guessing a random anime as clues are gradually revealed...",
                color=Color.green(),
            )
        )

        anime, synopsis_clue, genres = None, None, None
        async with ctx.channel.typing():
            animes: List = await get_user_anime_list(mal_username)
            if not animes or len(animes) == 0:
                await ctx.followup.send(
                    embed=Embed(
                        title="Error",
                        description=f"Could not retrieve anime list for user `{mal_username}` or the list is empty. Please check the username.",
                        color=Color.red(),
                    )
                )
                return

            random_idx = randint(0, len(animes) - 1)
            anime_id = animes[random_idx]["anime_id"]

            anime = await get_anime_by_id(anime_id)
            anime = anime.data

            synopsis_clue = await get_synopsis_clue(anime)
            genres = " ".join(f"`{genre.name}`" for genre in anime.genres)

        timer = 10
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

            if timer == 8:
                await ctx.send(embed=Embed(title="Clue #2: Genres", description=genres))

        await ctx.send(
            embed=Embed(
                title=anime.title,
                url=anime.url,
                description="This is the answer!",
                color=Color.brand_green(),
            )
        )

    @clues.command(description="submit your guess!")
    async def answer(self, ctx: ApplicationContext):
        pass


def setup(bot):
    bot.add_cog(AniClues(bot))
