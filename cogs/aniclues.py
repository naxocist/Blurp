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
from utils.customs.game_state import minigame_objects, players_games
from utils.customs.aniclues_comps import CluesClass
from utils.customs.commands import get_timer_embed

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
    async def init(self, ctx: ApplicationContext, mal_username: str):
        """
        Clues revelation order
        - General Info
            genres / themes
            status
            season, year
            rating
            studios
            episodes num
            MAL score
        - Specifics
            synopsis
            blured images
            title
        """

        if ctx.author in players_games:
            await ctx.respond(
                "You are currently in other minigame! Finish that first...",
                ephemeral=True,
            )

        await ctx.respond(
            embed=Embed(
                title="Anime Clues initialized!",
                description=f"You will be guessing a random anime from `[{mal_username}](https://myanimelist.net/profile/{mal_username})`!\n As clues are gradually revealed...",
                color=Color.green(),
            )
        )

        anime = None
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

        clue_obj = CluesClass(anime)
        minigame_objects.append(clue_obj)
        players_games[ctx.author] = clue_obj

        timer = clue_obj.timer
        timer_msg = await ctx.send(embed=get_timer_embed("Time left:", timer))
        crr_clue_embed = clue_obj.get_new_clue_embed(timer)
        await ctx.send(embed=crr_clue_embed)

        while timer > 0:
            await asyncio.sleep(1)
            timer -= 1

            # if timer % 5 == 0 or timer <= 5:
            await timer_msg.edit(embed=get_timer_embed("Time left:", timer))

            nxt_clue_embed = clue_obj.get_new_clue_embed(timer)
            if crr_clue_embed != nxt_clue_embed:
                await ctx.send(embed=nxt_clue_embed)
                crr_clue_embed = nxt_clue_embed

        await timer_msg.delete()

    @clues.command(description="submit your guess!")
    async def answer(self, ctx: ApplicationContext, anime_id: int):
        pass


def setup(bot):
    bot.add_cog(AniClues(bot))
