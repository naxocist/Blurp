import discord
from discord.ext import commands

from credentials import TEST_GUILD_ID, FRIEND_TEST_GUILD_ID


class MiniGames(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot
  
  @commands.slash_command(guild_ids=[TEST_GUILD_ID, FRIEND_TEST_GUILD_ID], description="Start a anime cycle game")
  async def cycle(self, ctx):
    """
    This game will assign each player a another random player.
    Everyone will pick an anime for their assigned player.
    Each player will then take turns to ask for a hint from other player about the anime they was assigned to.
    """

    await ctx.respond(embed=discord.Embed(
      title="Anime Cycle has been started!",
      color=discord.Color.green()
    ), view=discord.ui.View().add_item(
      discord.ui.Button(label="Join", style=discord.ButtonStyle.green, custom_id="join_cycle")
    ))


def setup(bot):
  bot.add_cog(MiniGames(bot))
