import discord
from discord import Bot, ApplicationContext, Embed, Color, Option
from discord.ext import commands

import asyncio
from math import floor

from utils.customs.game_state import minigame_objects, players_games
from utils.customs.whatnum_comps import BinarySearch
from credentials import guild_ids


class WhatNum(commands.Cog):

    fail_embed = lambda target: Embed(
        title="Failed",
        description=f"The number was **{target}**\nYou're not being optimal... You should've guessed it.\nMaybe look into [binary search](https://en.wikipedia.org/wiki/Binary_search)",
        color=Color.red(),
    )

    def __init__(self, bot: Bot):
        self.bot = bot

    binary_search = discord.SlashCommandGroup(
        "whatnum",
        "Try to guess a random number",
        guild_ids=guild_ids,
    )

    @binary_search.command(
        description="Try to guess a random number with least possible guess"
    )
    async def init(
        self,
        ctx: ApplicationContext,
        low=Option(int, "The lower bound (default = 1)", default=1),
        high=Option(int, "The upper bound (default = 100)", default=100),
    ):
        member = ctx.author

        if member in players_games:
            await ctx.respond(
                "You are in other minigames! Finish that first...", ephemeral=True
            )
            return

        if low >= high:
            await ctx.respond("low must less than high!", ephemeral=True)
            return

        bs_obj = BinarySearch(low, high)
        minigame_objects.append(bs_obj)
        players_games[member] = bs_obj

        await ctx.respond(
            embed=Embed(
                title=f"Guess a number from {bs_obj.low} to {bs_obj.high}",
                description=f"use `/whatnum guess <number>` to apply guess.\nI'll tell you whether your guess is less or greater than target number\n**You have {bs_obj.expected_guess_cnt} tries**",
                color=Color.green(),
            )
        )

        # print("Target number:", bs_obj.target)
        timer: int = floor(bs_obj.expected_guess_cnt ** (2.75))
        await ctx.send(f"You have {timer} seconds. Good luck!")

        while timer > 0:
            if bs_obj.success:
                break

            await asyncio.sleep(1)
            timer -= 1

        if timer == 0 or bs_obj.success == 1:
            await ctx.respond(embed=WhatNum.fail_embed(bs_obj.target))

        minigame_objects.remove(bs_obj)
        players_games.pop(member, None)

    @binary_search.command(description="Guess that random number!")
    async def guess(self, ctx: ApplicationContext, guess: int):
        member = ctx.author
        bs_obj: BinarySearch = players_games.get(member)

        if not bs_obj:
            await ctx.respond(f"You are not in any minigame!", ephemeral=True)
            return

        if not isinstance(bs_obj, BinarySearch):
            await ctx.respond(
                "You are not in a guess number minigame...", ephemeral=True
            )

        target = bs_obj.target
        bs_obj.guess_cnt += 1
        guess_left = bs_obj.expected_guess_cnt - bs_obj.guess_cnt

        msg = f"That's correct🤓 You've guessed **{bs_obj.guess_cnt}** time(s) to get to {target}"

        if guess == target:
            await ctx.respond(
                embed=Embed(title="Congrats!", description=msg, color=Color.green())
            )
            bs_obj.terminate(True)
            return

        if guess > target:
            msg = f"{guess} is too large... {guess_left} {"tries" if guess_left > 1 else "try"} left"
        elif guess < target:
            msg = f"{guess} is too small... {guess_left} {"tries" if guess_left > 1 else "try"} left"

        if guess_left == 0:
            bs_obj.terminate(False)
            return

        await ctx.respond(msg)

    @binary_search.command(description="For real!? plz don't")
    async def giveup(self, ctx: ApplicationContext):
        member = ctx.author
        bs_obj: BinarySearch = players_games.get(member)

        if not bs_obj:
            await ctx.respond(f"You can't give up on nothing...", ephemeral=True)
            return

        if not isinstance(bs_obj, BinarySearch):
            await ctx.respond(
                "You are not in a guess number minigame...", ephemeral=True
            )

        await ctx.respond("🤓☝️")
        bs_obj.terminate(False)


def setup(bot):
    bot.add_cog(WhatNum(bot))
