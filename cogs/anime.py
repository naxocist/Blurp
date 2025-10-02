import discord
from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Bot, Option
from nekosbest import Result

from typing import cast

from utils.apis.nekosbest import get_img, get_phrase, other_actions, self_actions
from utils.apis.jikanv4 import get_random_anime
from utils.customs.tools import make_anime_embed

from credentials import guild_ids


class Anime(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    # get a random anime based on jikan-v4 API

    @commands.slash_command(guild_ids=guild_ids, description="Get a random anime")
    async def anime(self, ctx: ApplicationContext):
        await ctx.defer()

        anime = await get_random_anime()
        embed = make_anime_embed(anime)
        response = await ctx.respond(embed=embed)
        await discord.Message.add_reaction(response, "📬")

    # expression emotions through gifs
    @commands.slash_command(guild_ids=guild_ids, description="Express your emotions")
    async def expression(
        self,
        ctx: ApplicationContext,
        action: str = Option(
            str, "What expression do you want to show?", choices=self_actions
        ),
    ):
        await ctx.defer()

        image = cast(Result, await get_img(action))
        phrase = get_phrase(action, ctx.author.mention)
        embed = Embed(image=image.url, color=Color.random())

        await ctx.respond(phrase, embed=embed)

    # actions to other members through gifs
    @commands.slash_command(
        guild_ids=guild_ids, description="Perform an action to another user"
    )
    async def action(
        self,
        ctx: ApplicationContext,
        member: Member,
        action: str = Option(
            str, "What action do you want to perform?", choices=other_actions
        ),
    ):
        await ctx.defer()
        image = cast(Result, await get_img(action))
        phrase = get_phrase(action, ctx.author.mention, member.mention)
        embed = Embed(image=image.url, color=Color.random())

        await ctx.respond(phrase, embed=embed)

    # get a random anime illustration
    @commands.slash_command(
        guild_ids=guild_ids, description="Get a random anime illustration"
    )
    async def art(
        self,
        ctx: ApplicationContext,
        choice: str = discord.Option(
            str,
            "Choose your type",
            choices=["husbando", "kitsune", "neko", "waifu"],
        ),
    ):
        await ctx.defer()

        result = cast(Result, await get_img(choice))

        image = result.url
        artist = result.artist_name or "Unknown"
        artist_href = result.artist_href or "N/A"
        source_url = result.source_url or "N/A"

        embed = Embed(
            title=f"Here is your {choice}!",
            description=f"Artist: **[{artist}]({artist_href})**\nVisit **[source]({
                source_url
            })!**",
            image=image,
            color=Color.random(),
        )

        await ctx.respond(embed=embed)


def setup(bot: Bot):
    bot.add_cog(Anime(bot))
