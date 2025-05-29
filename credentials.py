from dotenv import load_dotenv
import os
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")
NAXOCIST_GUILD_ID = os.getenv("NAXOCIST_GUILD_ID")
PINONT_HOME_GUILD_ID = os.getenv("PINONT_HOME_GUILD_ID")

r"""
powershell run dev command:
cls; $env:IS_DEV="True"; uv run .\main.py

cmd run dev command:
cls && set IS_DEV="True" && uv run .\main.py
"""
IS_DEV = os.getenv("IS_DEV", "False") == "True"

guild_ids = [NAXOCIST_GUILD_ID] if IS_DEV else None

if(IS_DEV):
  print("Running in development mode with guilds:", ", ".join(guild_ids))
