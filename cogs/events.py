import discord
from discord.ext import commands


class Events(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot

  @commands.Cog.listener()
  async def on_ready(self):
    print(f"We have logged in as {self.bot.user}")
  
  # Handle reacting 📬 to save an anime
  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload):
    member = payload.member
    if member is None or member.bot:
      return

    if payload.emoji.name != "📬":
      return

    channel = self.bot.get_channel(payload.channel_id)
    if not isinstance(channel, discord.TextChannel):
      return  # Ignore reactions in DMs or invalid channels

    try:
      message = await channel.fetch_message(payload.message_id)
      await member.send(embed=message.embeds[0])
    except discord.Forbidden:
      await channel.send(f"{member.mention}, I couldn't DM you. Please enable DMs.")
    except Exception:
      pass

  @commands.Cog.listener()
  async def on_application_command_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.respond("Missing required argument. Please check your command usage.")

    elif isinstance(error, commands.BadArgument):
      await ctx.respond("Invalid argument provided. Please check your command usage.")

    elif isinstance(error, commands.CommandOnCooldown):
      await ctx.respond(f"You're too fast! Try again in {error.retry_after:.2f} seconds.", ephemeral=True)

    else:
      print("An error occured:", error)


def setup(bot):
  bot.add_cog(Events(bot))
