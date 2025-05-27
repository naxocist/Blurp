import discord
from credentials import DISCORD_TOKEN


intents = discord.Intents.all()

bot = discord.Bot(description="The versatile anime related discord bot", intents=intents)
bot.activity = discord.Activity(name="anime", type=discord.ActivityType.watching)

cogs_list = ["animes", "events", "minigames"]

if __name__ == "__main__":
  print("Loading cogs...")
  for cog in cogs_list:
    try:
      bot.load_extension(f"cogs.{cog}")
      print(f"Loaded {cog} successfully.")
    except Exception as e:
      print(f"Failed to load {cog}: {e}")

  bot.run(DISCORD_TOKEN)