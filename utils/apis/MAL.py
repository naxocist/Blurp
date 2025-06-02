import requests
from pprint import pprint
from typing import List

import asyncio
from aiolimiter import AsyncLimiter


limiter = AsyncLimiter(max_rate=1, time_period=1)  # limit to 1 requests per 1 second


async def get_user_anime_list(username: str) -> List:
    url = f"https://myanimelist.net/animelist/{username}/load.json?offset=0&status=7"

    async with limiter:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, requests.get, url)

        if res.status_code != 200:
            return None

        data = res.json()
        return data
