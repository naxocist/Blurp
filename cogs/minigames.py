import discord
from discord.ext import commands

from credentials import TEST_GUILD_ID


class MiniGames(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot
  
  @commands.slash_command(guild_ids=[TEST_GUILD_ID], description="Start a anime cycle game")
  async def cycle(self, ctx):
    """
    This game will assign each player a another random player.
    Everyone will pick an anime for their assigned player.
    Each player will then take turns to ask for a hint from other player about the anime they was assigned to.
    """

    await ctx.respond("This feature is under development. Stay tuned for updates!")


def setup(bot):
  bot.add_cog(MiniGames(bot))
