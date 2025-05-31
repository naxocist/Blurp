from jikanpy import Jikan
from dotmap import DotMap

import asyncio
from aiolimiter import AsyncLimiter

jikan = Jikan()
limiter = AsyncLimiter(max_rate=3, time_period=1)  # limit to 3 requests per 1 second


async def get_random_anime() -> DotMap:
    async with limiter:
        # Convert the synchronous Jikan call to an asynchronous one
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, jikan.random, "anime")
        return DotMap(res)


async def get_anime_characters(mal_id: int) -> DotMap:
    async with limiter:
        # Convert the synchronous Jikan call to an asynchronous one
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, jikan.anime, mal_id, "characters")
        return DotMap(res)


async def get_anime_by_id(anime_id):
    try:
        async with limiter:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, jikan.anime, anime_id)
            return DotMap(res)
    except Exception:
        return None
