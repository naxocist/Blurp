from dotmap import DotMap
from discord import Embed
import discord

from typing import List
import asyncio

from utils.apis.typhoon import get_synopsis_clue
from utils.customs.commands import blur_image_from_url


class CluesClass:
    clues_embed = []
    clues_reveal_after: List[int] = [0, 5, 5, 5, 5]
    delay = 20
    timer = sum(clues_reveal_after) + delay

    def __init__(self, anime: DotMap):
        self.crr_clue_idx: int = 0
        self.anime = anime
        self.just_answered = (
            0  # 0: not yet answered, 1: answered (wrong), 2: answered (right)
        )
        self.prv_clue_time = 0
        self.skip = False

        genres = " ".join(f"`{genre.name}`" for genre in anime.genres) or "N/A"
        themes = " ".join(f"`{theme.name}`" for theme in anime.themes) or "`N/A`"
        studios = " ".join(f"`{studio.name}`" for studio in anime.studios) or "N/A"
        producers = (
            " ".join(f"`{producer.name}`" for producer in anime.producers) or "N/A"
        )
        season = anime.season
        year = anime.year
        episodes = anime.episodes or "`N/A`"
        score = f"`{anime.score}`/10" or "`N/A`"
        ranked = f"#{anime.rank}" or "N/A"

        CluesClass.clues_embed = [
            # Clue #1: Genres, Themes, Season/Year
            Embed(title="Clue #1: Just basic information")
            .add_field(name="Genres", value=genres, inline=True)
            .add_field(name="Themes", value=themes, inline=True)
            .add_field(
                name="Season/Year",
                value=f"`{season.capitalize() + " " + str(year) if season and year else "N/A"}`",
                inline=True,
            ),
            # Clue #2: Eps, Score, Ranked
            Embed(title="Clue #2: Maybe some stats will help")
            .add_field(name="Episodes", value=f"`{episodes}` episodes", inline=True)
            .add_field(name="Score", value=score, inline=True)
            .add_field(name=f"Ranked: `{ranked}`", value="", inline=True),
            # Clue #3: Studio, Producers
            Embed(title="Clue #3: Who created this!?")
            .add_field(name="Studios", value=studios)
            .add_field(name="Producers", value=producers),
            # Clue #4: Synopsis
            Embed(title="Clue #4: You should recognize this"),
            # Clue #5: Image Cover
            Embed(title="Clue #5: Okay..."),
        ]

        self.answered_event = asyncio.Event()

    async def fetch_clues(self):
        synopsis_clue = await get_synopsis_clue(self.anime)
        CluesClass.clues_embed[3].add_field(
            name="Summarized synopsis", value=synopsis_clue
        )

        image_url = self.anime.images.jpg.image_url
        file_buffer = blur_image_from_url(image_url, 50)
        self.file = discord.File(fp=file_buffer, filename="blurred.png")

        CluesClass.clues_embed[4].set_image(url="attachment://blurred.png")

    def get_new_clue_embed(self, timer: int) -> Embed:
        time_passed = CluesClass.timer - timer
        nxt_clue_idx = self.crr_clue_idx + 1

        time_after_prv_clue = time_passed - self.prv_clue_time
        if (
            nxt_clue_idx == len(CluesClass.clues_embed)
            or time_after_prv_clue != CluesClass.clues_reveal_after[nxt_clue_idx]
        ) and not self.skip:
            return CluesClass.clues_embed[self.crr_clue_idx]

        self.skip = False
        self.crr_clue_idx += 1
        self.prv_clue_time = time_passed
        return CluesClass.clues_embed[nxt_clue_idx]

    def skip_clue(self):
        self.skip = True
