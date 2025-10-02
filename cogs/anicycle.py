from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Bot
from dotmap import DotMap
import discord


from utils.apis.jikanv4 import get_anime_by_id

from utils.customs.states import players_games  # shared in-memory game state
from utils.customs.anicycle.comps import CycleClass
from utils.customs.anicycle.logic import (
    init_phase,
    random_phase,
    pick_phase,
    game_phase,
)

from credentials import guild_ids


class AniCycle(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    cycle = discord.SlashCommandGroup(
        "cycle", "anime cycle game commands", guild_ids=guild_ids
    )

    @cycle.command(description="Initialize an anime cycle game")
    async def init(self, ctx: ApplicationContext):
        await ctx.defer()

        cycle_obj = await init_phase(ctx)

        if not cycle_obj:
            return

        # DEMO data
        # cycle_obj.add_player(ctx.author)
        # cycle_obj.add_player(self.bot.user)
        # cycle_obj.player_animes[ctx.author] = DotMap(
        #     dict(
        #         title="Aharen-san wa Hakarenai Season 2",
        #         url="https://myanimelist.net/anime/59466/Aharen-san_wa_Hakarenai_Season_2",
        #         mal_id=59466,
        #     )
        # )

        pick_msg, pick_view = await random_phase(ctx, cycle_obj)
        await pick_phase(ctx, cycle_obj, pick_msg, pick_view)
        await game_phase(ctx, cycle_obj)

    @cycle.command(description="Pick an anime for your assigned player")
    async def pick(self, ctx: ApplicationContext, anime_id: int):
        """
        This command should be used in "picking" phase
        Pick an anime for assigned player using MAL anime id.
        """
        member: Member = ctx.author
        cycle_obj: CycleClass = players_games.get(member)

        if not cycle_obj:
            await ctx.respond("You are not in any anime cycle game.", ephemeral=True)
            return

        if cycle_obj.current_phase() != "picking":
            await ctx.respond("The game is not in the picking phase!", ephemeral=True)
            return

        result = await get_anime_by_id(anime_id)
        if not result:
            await ctx.respond("Invalid anime id was provided.", ephemeral=True)
            return

        title, url, mal_id, image_url = (
            result.data.title,
            result.data.url,
            result.data.mal_id,
            result.data.images.jpg.image_url,
        )

        target: Member = cycle_obj.targets[
            member
        ]  # get member object of assigned player

        # assigned that player a dotmapped compact anime info
        cycle_obj.player_animes[target] = DotMap(
            dict(title=title, url=url, mal_id=mal_id)
        )

        pick_embed = Embed(
            description=f"You picked **[{title}]({url})** for {target.mention}!",
            image=image_url,
            color=Color.nitro_pink(),
        )
        await ctx.respond(embed=pick_embed, ephemeral=True)

        # trigger pick event
        cycle_obj.add_picked(member)

    @cycle.command(description="Submit your answer here!")
    async def answer(self, ctx: ApplicationContext, anime_id: int):
        """
        This command should be used in "turns" phase
        Member will use this command to submit their answer
        """
        member: Member = ctx.author
        cycle_obj: CycleClass = players_games.get(member)

        if not cycle_obj:
            await ctx.respond("You are not in any anime cycle game.", ephemeral=True)
            return

        if not isinstance(cycle_obj, CycleClass):
            await ctx.respond("You are not in anicycle minigame...", ephemeral=True)
            return

        if cycle_obj.current_phase() != "turns":
            await ctx.respond("The game is not in the turns phase!", ephemeral=True)
            return

        if member != cycle_obj.current_player():
            await ctx.respond("It's not your turn yet!", ephemeral=True)
            return

        result = await get_anime_by_id(anime_id)
        if not result:
            await ctx.respond("Invalid anime id was provided.", ephemeral=True)
            return

        title, url, mal_id, image_url = (
            result.data.title,
            result.data.url,
            result.data.mal_id,
            result.data.images.jpg.image_url,
        )

        target: DotMap = cycle_obj.player_animes[
            member
        ]  # retrieve player's assigned anime

        correct = target.mal_id == mal_id
        guessed = f"{member.mention} guessed [{title}]({url})\n"
        embed = Embed(image=image_url)

        if correct:
            cycle_obj.just_answered = 1
            guessed += "**Correct!** 🤓"
            embed.color = Color.brand_green()
            cycle_obj.add_done(member)
            cycle_obj.turn_done[member] = cycle_obj.round
        else:
            cycle_obj.just_answered = 2
            guessed += "**Not quite right... Try again!** 🥹"
            embed.color = Color.brand_red()

        embed.description = guessed
        answer_msg = await ctx.respond(embed=embed)
        cycle_obj.answered_event.set()  # trigger answered flag

        msg = await answer_msg.original_response()
        await msg.delete(delay=5)


def setup(bot):
    bot.add_cog(AniCycle(bot))
