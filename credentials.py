from dotenv import load_dotenv
import os

load_dotenv()

BLURP_DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
EXAMPLE_DISCORD_TOKEN = os.getenv("EXAMPLE_DISCORD_TOKEN")
TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")
NAXOCIST_GUILD_ID = os.getenv("NAXOCIST_GUILD_ID")
PINONT_HOME_GUILD_ID = os.getenv("PINONT_HOME_GUILD_ID")
MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID")
MAL_CLIENT_SECRET = os.getenv("MAL_CLIENT_SECRET")


r"""

powershell run dev command
(IS_DEV persists throughout powershell session)
cls; $env:IS_DEV="True"; uv run .\main.py

"""
guild_ids = None
IS_DEV = os.getenv("IS_DEV")
if IS_DEV:
    # Development Variable
    guild_ids = [NAXOCIST_GUILD_ID]
    BLURP_DISCORD_TOKEN = EXAMPLE_DISCORD_TOKEN

    if guild_ids is not None:
        print(
            "Running in development mode with guilds:",
            ", ".join(g for g in guild_ids if g is not None),
        )
    else:
        print("Running in development mode but no guild IDs are set.")
else:
    print("Running on production Mode")
