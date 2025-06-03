import discord
from discord.ext import commands
from discord import ApplicationContext, Embed, Color, Bot, Member

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
        "clues",
        "Guessing random anime from a MAL profile minigame based on clues",
        guild_ids=guild_ids,
    )

    @clues.command(description="start guessing random anime from given MAL profile!")
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
        await ctx.defer()

        if ctx.author in players_games:
            await ctx.respond(
                "You are currently in other minigame! Finish that first...",
                ephemeral=True,
            )
            return

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
        anime_id = animes[random_idx]["node"]["id"]

        print("random id:", anime_id)
        anime = await get_anime_by_id(anime_id)
        anime = anime.data

        clue_obj = CluesClass(anime)
        await clue_obj.get_synopsis_clue()

        await ctx.respond(
            embed=Embed(
                title="Anime Clues initialized!",
                description=f"You will be guessing a random anime from [{mal_username}](https://myanimelist.net/profile/{mal_username})!\n As clues are gradually revealed...",
                color=Color.green(),
            )
        )

        minigame_objects.append(clue_obj)
        players_games[ctx.author] = clue_obj

        timer = clue_obj.timer
        timer_msg = await ctx.send(embed=get_timer_embed("Time left:", timer))
        crr_clue_embed = clue_obj.get_new_clue_embed(timer)
        await ctx.send(embed=crr_clue_embed)

        while timer > 0:

            await asyncio.wait(
                [
                    asyncio.create_task(asyncio.sleep(1)),
                    asyncio.create_task(clue_obj.answered_event.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            clue_obj.answered_event.clear()

            if clue_obj.just_answered:
                if clue_obj.just_answered == 2:
                    # correct answer
                    break

                # incorrect answer
                clue_obj.skip_clue()
                clue_obj.just_answered = 0
            else:
                # Only decrement time if 1 second passed (not interrupted early)
                timer -= 1

            if timer % 5 == 0 or timer <= 5:
                await timer_msg.edit(embed=get_timer_embed("Time left:", timer))

            nxt_clue_embed = clue_obj.get_new_clue_embed(timer)
            if crr_clue_embed != nxt_clue_embed:
                await ctx.send(embed=nxt_clue_embed)
                crr_clue_embed = nxt_clue_embed

        await timer_msg.delete()

        minigame_objects.remove(clue_obj)
        players_games.pop(ctx.author)

    @clues.command(description="submit your guess!")
    async def answer(self, ctx: ApplicationContext, anime_id: int):
        member: Member = ctx.author
        clues_obj = players_games.get(member)

        if not clues_obj:
            await ctx.respond(f"You are not in any minigame!", ephemeral=True)
            return

        if not isinstance(clues_obj, CluesClass):
            await ctx.respond("Finish other minigame first...", ephemeral=True)

        anime = clues_obj.anime
        if anime_id == anime.mal_id:
            await ctx.respond(
                f"You are correct!, clue(s) used {clues_obj.crr_clue_idx + 1}",
                embed=Embed(
                    title=anime.title, url=anime.url, image=anime.images.jpg.image_url
                ),
            )
            clues_obj.just_answered = 2  # answered correctly
        else:
            await ctx.respond(
                f"Nah, it's not quite right. Revealing next clue...",
            )
            clues_obj.just_answered = 1

        clues_obj.answered_event.set()  # trigger answered flag


def setup(bot):
    bot.add_cog(AniClues(bot))
