import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from aiolimiter import AsyncLimiter
from jikanpy import Jikan

limiter = AsyncLimiter(max_rate=3, time_period=1)  # limit to 3 requests per 1 second
executor = ThreadPoolExecutor(max_workers=5)  # limit number of threads

jikan = Jikan()


async def get_random_anime() -> dict[str, Any]:
    try:
        async with limiter:
            loop = asyncio.get_running_loop()
            anime = await loop.run_in_executor(executor, lambda: jikan.random("anime"))
            return anime.get("data", {})
    except:
        return {}


async def get_anime_characters(mal_id: int) -> list[dict[str, Any]]:
    try:
        async with limiter:
            loop = asyncio.get_running_loop()
            characters = await loop.run_in_executor(
                executor, lambda: jikan.anime(mal_id, "characters")
            )
            return characters.get("data", [])
    except:
        return []


async def get_anime_by_id(mal_id: int) -> dict[str, Any]:
    try:
        async with limiter:
            loop = asyncio.get_running_loop()
            anime = await loop.run_in_executor(executor, lambda: jikan.anime(mal_id))
            return anime["data"]
    except:
        return {}
