import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO

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

    if timeout <= 0:
        raise "timeout must be positive value!"

    timer_msg = await ctx.send(embed=get_timer_embed(title_prefix, timeout))
    while timeout > 0:
        await asyncio.sleep(1)  # ping every 1s
        timeout -= 1

        if timeout == 0:
            await timer_msg.delete()
            return

        elif timeout % interval == 0 or timeout <= 5:
            await timer_msg.edit(embed=get_timer_embed(title_prefix, timeout))

        if check_done and check_done():
            if timeout > 0:
                await timer_msg.delete()
            return


def blur_image_from_url(url, blur_strength=25):
    # Download image
    response = requests.get(url)
    image = Image.open(BytesIO(response.content)).convert("RGB")

    # Convert to OpenCV format (numpy array)
    img_cv = np.array(image)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

    # Apply Gaussian blur
    blurred_cv = cv2.GaussianBlur(img_cv, (blur_strength | 1, blur_strength | 1), 0)

    # Convert back to PIL Image
    blurred_rgb = cv2.cvtColor(blurred_cv, cv2.COLOR_BGR2RGB)
    result_image = Image.fromarray(blurred_rgb)

    # Save to memory
    buffer = BytesIO()
    result_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
