import os
from typing import Optional
from dotenv import load_dotenv

# === Determine Environment ===
ENV = os.getenv("ENV", "production").lower()
IS_DEV = ENV == "dev"

env_file = ".env.development" if IS_DEV else ".env.production"

if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)
    print(f"Loaded variables from {env_file}")
else:
    print(f"No {env_file} found. Using system environment variables.")

REQUIRED_KEYS = ["DISCORD_BOT_TOKEN", "TYPHOON_API_KEY", "MAL_CLIENT_SECRET", "MAL_CLIENT_ID"]
for key in REQUIRED_KEYS:
    if not os.getenv(key):
        raise RuntimeError(f"Missing critical variable: {key}")

# === Constants / Environment Variables ===
DISCORD_BOT_TOKEN: str | None = os.getenv("DISCORD_BOT_TOKEN")

NAXOCIST_GUILD_ID: str | None = os.getenv("NAXOCIST_GUILD_ID")
PINONT_HOME_GUILD_ID: str | None = os.getenv("PINONT_HOME_GUILD_ID")

TYPHOON_API_KEY: str | None = os.getenv("TYPHOON_API_KEY")
MAL_CLIENT_ID: str | None = os.getenv("MAL_CLIENT_ID")
MAL_CLIENT_SECRET: str | None = os.getenv("MAL_CLIENT_SECRET")

# === Guild IDs Handling ===
guild_ids: Optional[list[int]] = []

if IS_DEV:
    print("🔧 Dev mode!")
    raw_guilds = [NAXOCIST_GUILD_ID]

    for gid in raw_guilds:
        if gid:
            try:
                guild_ids.append(int(gid))
            except ValueError:
                print(f"⚠️ Invalid guild ID in environment: {gid}")

    if guild_ids:
        print(f"✅ Guilds registered for dev mode: {', '.join(map(str, guild_ids))}")
    else:
        print("⚠️ No valid guild IDs set for dev mode.")
else:
    guild_ids = None
    print("🚀 Production mode!")
