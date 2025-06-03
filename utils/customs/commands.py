from typing import Optional, Callable
from discord import ApplicationContext, Embed, Color
import asyncio


def get_timer_embed(title_prefix, timeout) -> Embed:
    return Embed(title=f"{title_prefix} {timeout} seconds", color=Color.dark_magenta())


async def count_down_timer(
    ctx: ApplicationContext,
    timeout: int,
    *,
    title_prefix: str = "Time left:",
    interval: int = 5,
    check_done: Optional[Callable] = None,
):

    timer_msg = await ctx.send(embed=get_timer_embed(title_prefix, timeout))
    while timeout > 0:
        await asyncio.sleep(1)  # ping every 1s
        timeout -= 1

        if timeout == 0:
            await timer_msg.delete()
        elif timeout % interval == 0 or timeout <= 5:
            await timer_msg.edit(embed=get_timer_embed(title_prefix, timeout))

        if check_done and check_done():
            if timeout > 0:
                await timer_msg.delete()
            break

    await timer_msg.delete()
