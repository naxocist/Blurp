from jikanpy import Jikan
from dotmap import DotMap

import asyncio
from aiolimiter import AsyncLimiter

jikan = Jikan()
limiter = AsyncLimiter(max_rate=3, time_period=1) # 3 requests per 1 second


async def get_random_anime():
  """
  Fetches a random anime from Jikan API and convert it to DotMap object.
  """
  async with limiter:
    # Convert the synchronous Jikan call to an asynchronous one
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, jikan.random, "anime")
    return DotMap(data)


async def get_anime_by_id(anime_id):
  """
  Fetches an anime by its ID from Jikan API and convert it to DotMap object.
  """

  try:
    async with limiter:
      loop = asyncio.get_running_loop()
      data = await loop.run_in_executor(None, jikan.anime, anime_id)
      return DotMap(data)
  except Exception:
    return None
