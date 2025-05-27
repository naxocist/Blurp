import discord
from discord.ext import commands
from utils.nekosbest import get_img, to_is_phrase, actions_to_others, expressions

from dotenv import load_dotenv
import os
load_dotenv()
test_guild_id = os.getenv("TEST_GUILD_ID")


class Animes(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot
  
  @commands.slash_command(guild_ids=[test_guild_id], description="Show your expression")
  async def expression(self, ctx, action: str = discord.Option(str, "What expression do you want to show?", choices=expressions)):
    image = await get_img(action)
    is_phrase_action = to_is_phrase(action)
    embed = discord.Embed(
      color=discord.Color.random(),
      image=image.url
    )
    await ctx.respond(f"{ctx.author.mention} {is_phrase_action}!", embed=embed)

  @commands.slash_command(guild_ids=[test_guild_id], description="Perform an action to another user") 
  async def action(self, ctx, member: discord.Member, action: str = discord.Option(str, "What action do you want to perform?", choices=actions_to_others)):
    image = await get_img(action)
    embed = discord.Embed(
      color=discord.Color.random(),
      image=image.url
    )

    if action == "dance": action += " with"
    await ctx.respond(f"{ctx.author.mention} wants to {action} {member.mention}!", embed=embed)

  @commands.slash_command(guild_ids=[test_guild_id], description="Get a random waifu image")
  async def waifu(self, ctx, choice: str = discord.Option(str, "Choose your type", choices=["husbando", "kitsune", "neko", "waifu"])):
    image = await get_img(choice)
    embed = discord.Embed(
      title=choice,
      color=discord.Color.random(),
      image=image.url
    )
    await ctx.respond(embed=embed)

  @commands.slash_command(guild_ids=[test_guild_id], description="Get a random anime")
  async def anime(self, ctx):
    embed = discord.Embed(
      title="Anime",
      description="This is an anime embed!",
      color=discord.Color.blue()
    )
    await ctx.respond(embed=embed)


def setup(bot):
  bot.add_cog(Animes(bot))
