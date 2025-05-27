from discord.ext import commands


class Events(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot

  @commands.Cog.listener()
  async def on_ready(self):
    print(f"We have logged in as {self.bot.user}")

  @commands.Cog.listener()
  async def on_command_error(self, ctx, error):
    if isinstance(error, commands.CommandNotFound):
      return
    elif isinstance(error, commands.MissingRequiredArgument):
      await ctx.send("Missing required argument. Please check your command usage.")
    elif isinstance(error, commands.BadArgument):
      await ctx.send("Invalid argument provided. Please check your command usage.")
    else:
      await ctx.send(f"An error occurred: {error}")


def setup(bot):
  bot.add_cog(Events(bot))
