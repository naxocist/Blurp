import asyncio
from typing import Union

from nekosbest import Client, Result

client = Client()

async def get_img(type: str, amount: int = 1) -> Union[Result, list[Result]]:
    result = await client.get_image(type, amount)
    print(result)

loop = asyncio.get_event_loop()

loop.run_until_complete(get_img("lurk"))
# loop.run_until_complete(get_img("neko", 2))

loop.close()
