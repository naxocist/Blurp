import os
from dotenv import load_dotenv


# === Load environment variables ===
IS_DEV = os.getenv("ENV") == "dev"
env_file = ".env.development" if IS_DEV else ".env.production"
load_dotenv(dotenv_path=env_file)


# === Development / Production Mode Handling ===
""" 
cls; $env:ENV="dev"; uv run .\main.py 
"""


# === Constants ===
GUILD_IDS = None
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

NAXOCIST_GUILD_ID = os.getenv("NAXOCIST_GUILD_ID")
PINONT_HOME_GUILD_ID = os.getenv("PINONT_HOME_GUILD_ID")

TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")
MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID")
MAL_CLIENT_SECRET = os.getenv("MAL_CLIENT_SECRET")


print(DISCORD_BOT_TOKEN)
if IS_DEV:
    print("🔧 Running in development mode.")
    GUILD_IDS = [gid for gid in [NAXOCIST_GUILD_ID] if gid]

    if GUILD_IDS:
        print("✅ Guilds registered for dev mode:", ", ".join(GUILD_IDS))
    else:
        print("⚠️ No guild IDs set for dev mode.")
else:
    print("🚀 Running in production mode.")
