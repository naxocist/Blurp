import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from discord import ApplicationContext, Embed, Color

from typing import Any, Callable
import asyncio


def make_anime_embed(anime: dict[str, Any]) -> Embed:
    title = anime.get("title", "N/A")
    url = anime.get("url", "")
    image_url = anime.get("images", {}).get("jpg", {}).get("image_url", "")

    genres_list = anime.get("genres", [])
    genres = " ".join(f"`{g['name']}`" for g in genres_list) if genres_list else "`N/A`"

    season = anime.get("season")
    year = anime.get("year")
    season_str = f"{season.capitalize()} {year}" if season and year else "N/A"

    episodes = anime.get("episodes") or "N/A"
    score = f"`{anime.get('score', 'N/A')}`/10"
    ranked = f"#{anime.get('rank', 'N/A')}"

    embed = Embed(title=title, url=url, color=Color.random())

    if image_url:
        embed.set_image(url=image_url)

    embed.add_field(name="Genres", value=genres, inline=False)
    embed.add_field(name="Season", value=f"`{season_str}`", inline=True)
    embed.add_field(name="Length", value=f"`{episodes}` episodes", inline=True)
    embed.add_field(name="Score", value=score, inline=True)
    embed.add_field(name="Ranked", value=ranked, inline=False)

    return embed


def blur_image_from_url(url: str, blur_strength: int = 25) -> BytesIO:
    """
    Downloads an image from a URL, applies Gaussian blur, and returns it as a BytesIO buffer.

    Args:
        url (str): Image URL.
        blur_strength (int): Strength of the Gaussian blur. Must be positive odd integer.

    Returns:
        BytesIO: Blurred image in PNG format.
    """
    # Download and open the image
    response = requests.get(url)
    response.raise_for_status()  # Raise error if download fails
    image = Image.open(BytesIO(response.content)).convert("RGB")

    # Convert to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Ensure blur kernel is odd
    ksize = max(1, blur_strength | 1)

    # Apply Gaussian blur
    blurred_cv = cv2.GaussianBlur(img_cv, (ksize, ksize), 0)

    # Convert back to PIL Image
    result_image = Image.fromarray(cv2.cvtColor(blurred_cv, cv2.COLOR_BGR2RGB))

    # Save to BytesIO buffer
    buffer = BytesIO()
    result_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def get_timer_embed(title_prefix, timeout) -> Embed:
    return Embed(title=f"{title_prefix} {timeout} seconds", color=Color.dark_magenta())


async def count_down_timer(
    ctx: ApplicationContext,
    timeout: int,
    *,
    title_prefix: str = "Time left:",
    interval: int = 5,
    check_done: Callable | None = None,
):
    if timeout <= 0:
        raise Exception("timeout must be positive value!")

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
