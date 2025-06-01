from typing import Optional, Callable
from discord import ApplicationContext, Embed, Color
import asyncio


async def count_down_timer(
    ctx: ApplicationContext,
    timeout: int,
    *,
    title_prefix: str = "Time left:",
    interval: int = 5,
    check_done: Optional[Callable] = None,
):

    timer_msg = await ctx.send(
        embed=Embed(
            title=f"{title_prefix} {timeout} seconds", color=Color.dark_magenta()
        )
    )
    while timeout > 0:
        await asyncio.sleep(1)  # ping every 1s
        timeout -= 1

        if timeout == 0:
            await timer_msg.delete()
        elif timeout % interval == 0 or timeout <= 5:
            await timer_msg.edit(
                embed=Embed(
                    title=f"{title_prefix} {timeout} seconds",
                    color=Color.dark_magenta(),
                )
            )

        if check_done and check_done():
            if timeout > 0:
                await timer_msg.delete()
            break
