import discord

from credentials import DISCORD_BOT_TOKEN
from logging_config import setup_logging

setup_logging()


intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(
    description="The versatile anime related discord bot", intents=intents
)

bot.activity = discord.Activity(type=discord.ActivityType.watching, name="anime")

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("Discord TOKEN is required")
        exit()

    print("Loading cogs...")
    for cog in ["anime", "events", "anicycle", "aniclues", "whatnum"]:
        try:
            _ = bot.load_extension(f"cogs.{cog}")
            print(f"Loaded {cog}.py successfully.")
        except Exception as e:
            print(f"Failed to load {cog}.py: {e}")
    bot.run(DISCORD_BOT_TOKEN)
