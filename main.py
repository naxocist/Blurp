import discord
from credentials import DISCORD_TOKEN
from logging_config import setup_logging

setup_logging()

intents = discord.Intents.all()

bot = discord.Bot(
    description="The versatile anime related discord bot", intents=intents
)
bot.activity = discord.Activity(name="anime", type=discord.ActivityType.watching)

cogs_list = ["anime", "events", "anicycle", "aniclues", "minigames"]

if __name__ == "__main__":

    print("Loading cogs...")
    for cog in cogs_list:
        try:
            bot.load_extension(f"cogs.{cog}")
            print(f"Loaded {cog}.py successfully.")
        except Exception as e:
            print(f"Failed to load {cog}.py: {e}")
            break

    bot.run(DISCORD_TOKEN)
