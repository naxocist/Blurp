import os
from dotenv import load_dotenv

# === Determine Environment ===
IS_DEV = os.getenv("ENV", "production").lower() == "dev"
env_file = ".env.development" if IS_DEV else ".env.production"

if not load_dotenv(dotenv_path=f"./env/{env_file}"):
    raise FileNotFoundError(f"Environment file '{env_file}' not found in ./env/")

# === Constants / Environment Variables ===
DISCORD_BOT_TOKEN: str | None = os.getenv("DISCORD_BOT_TOKEN")

NAXOCIST_GUILD_ID: str | None = os.getenv("NAXOCIST_GUILD_ID")
PINONT_HOME_GUILD_ID: str | None = os.getenv("PINONT_HOME_GUILD_ID")

TYPHOON_API_KEY: str | None = os.getenv("TYPHOON_API_KEY")
MAL_CLIENT_ID: str | None = os.getenv("MAL_CLIENT_ID")
MAL_CLIENT_SECRET: str | None = os.getenv("MAL_CLIENT_SECRET")

# === Guild IDs Handling ===
guild_ids: list[int] = []

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
    print("🚀 Production mode!")
