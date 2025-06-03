import requests

from pprint import pprint
from typing import List
import asyncio
from aiolimiter import AsyncLimiter
import functools

from credentials import MAL_CLIENT_ID


limiter = AsyncLimiter(max_rate=1, time_period=1)  # limit to 1 requests per 1 second


async def get_user_anime_list(mal_username: str) -> List:
    headers = {"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
    url = f"https://api.myanimelist.net/v2/users/{mal_username}/animelist?&limit=1000&nsfw=true"

    animes = []
    while True:
        async with limiter:
            loop = asyncio.get_running_loop()
            req_func = functools.partial(requests.get, url, headers=headers)
            res = await loop.run_in_executor(None, req_func)

            if res.status_code != 200:
                print(res.status_code)
                return None

            res = res.json()
            data = res["data"]
            animes.extend(data)
            url = res.get("paging", {}).get("next")
            if not url:
                break

    return animes
