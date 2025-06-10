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

from credentials import guild_ids


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
            genres
            themes
            season, year

            episodes num
            MAL score
            ranked

            studios
            producers
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
        await clue_obj.setup_clues()

        await ctx.respond(
            embed=Embed(
                title="Anime Clues initialized!",
                description=f"You will be guessing a random anime from [{mal_username}](https://myanimelist.net/profile/{mal_username}) profile!\n As clues are gradually revealed...",
                color=Color.blurple(),
            )
        )

        minigame_objects.append(clue_obj)
        players_games[ctx.author] = clue_obj

        # Send first clue & timer
        crr_clue_embed = clue_obj.get_current_embed()
        await ctx.send(embed=crr_clue_embed)
        timer = clue_obj.timer
        timer_msg = await ctx.send(
            embed=get_timer_embed("Time until next clue: ", timer)
        )

        while True:

            sleep_task = asyncio.create_task(asyncio.sleep(1))
            answered_task = asyncio.create_task(clue_obj.answered_event.wait())
            done, pending = await asyncio.wait(
                [sleep_task, answered_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            async def next_clue_and_new_timer():
                nonlocal timer, timer_msg
                clue_obj.next_clue()
                clue_obj.just_answered = 0

                crr_clue_embed = clue_obj.get_current_embed()
                await ctx.send(
                    file=clue_obj.file if clue_obj.crr_clue_idx == 4 else None,
                    embed=crr_clue_embed,
                )

                await timer_msg.delete()
                timer = clue_obj.timer
                timer_msg = await ctx.send(
                    embed=get_timer_embed(
                        f"{"Time until solution: " if clue_obj.is_last_clue() else "Time until next clue: "}",
                        timer,
                    )
                )

            if answered_task in done:

                clue_obj.answered_event.clear()

                # correct answer or out of clues, terminate
                if clue_obj.just_answered == 2 or clue_obj.is_last_clue():
                    await timer_msg.delete()
                    break

                # incorrect answer, send next clue & new timer
                await next_clue_and_new_timer()
            else:
                timer -= 1

                # timeout,
                if timer == 0:
                    # out of clues
                    if clue_obj.is_last_clue():
                        await timer_msg.delete()
                        break
                    # send next clue & new timer
                    await next_clue_and_new_timer()

            if timer % 5 == 0 or timer <= 5:
                await timer_msg.edit(
                    embed=get_timer_embed(
                        f"{"Time until solution: " if clue_obj.is_last_clue() else "Time until next clue: "}",
                        timer,
                    ),
                )

        if clue_obj.is_last_clue():
            await ctx.send(
                embed=Embed(
                    title=anime.title,
                    description="This is the answer... Try again next time!",
                    url=anime.url,
                    image=anime.images.jpg.image_url,
                    color=Color.brand_red(),
                )
            )

        minigame_objects.remove(clue_obj)
        players_games.pop(ctx.author)

    @clues.command(description="submit your guess!")
    async def answer(self, ctx: ApplicationContext, anime_id: int):
        member: Member = ctx.author
        clues_obj: CluesClass = players_games.get(member)

        if not clues_obj:
            await ctx.respond(f"You are not in any minigame!", ephemeral=True)
            return

        if not isinstance(clues_obj, CluesClass):
            await ctx.respond("You are not in aniclues minigame...", ephemeral=True)
            return

        anime = clues_obj.anime
        if anime_id == anime.mal_id:
            await ctx.respond(
                f"You're right!, used {clues_obj.crr_clue_idx + 1} clue(s)",
                embed=Embed(
                    title=anime.title,
                    url=anime.url,
                    image=anime.images.jpg.image_url,
                    color=Color.green(),
                ),
            )
            clues_obj.just_answered = 2  # correct answer
        else:
            answered_anime = await get_anime_by_id(anime_id)
            if not answered_anime:
                await ctx.respond("Invaid anime id...", ephemeral=True)
                return

            answered_anime = answered_anime.data
            await ctx.respond(
                f"Nah, [{answered_anime.title}]({answered_anime.url}) is not quite right. Revealing next clue...",
            )
            clues_obj.just_answered = 1  # incorrect answer

        clues_obj.answered_event.set()  # trigger answered flag


def setup(bot):
    bot.add_cog(AniClues(bot))
