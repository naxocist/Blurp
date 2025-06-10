from dotmap import DotMap
from discord import Embed
from discord import Color
import discord

from typing import List
import asyncio

from utils.apis.typhoon import get_synopsis_clue
from utils.customs.commands import blur_image_from_url


class CluesClass:
    clues_embed = []
    clues_reveal_after: List[int] = [60, 60, 60, 60, 30]
    delay = 20

    def __init__(self, anime: DotMap):
        self.crr_clue_idx: int = 0
        self.anime = anime

        self.timer = CluesClass.clues_reveal_after[0]

        # 0: not yet answered, 1: answered (wrong), 2: answered (right)
        self.just_answered = 0
        self.answered_event = asyncio.Event()

    async def setup_clues(self):
        description = "use `/clues answer <anime_id>` to answer!"
        anime = self.anime
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

        synopsis_clue = await get_synopsis_clue(self.anime)
        image_url = self.anime.images.jpg.image_url
        file_buffer = blur_image_from_url(image_url, 50)
        self.file = discord.File(fp=file_buffer, filename="blurred.png")

        CluesClass.clues_embed = [
            # Clue #1: Genres, Themes, Season/Year
            Embed(
                title="Clue #1: Basic information",
                color=Color.red(),
                description=description,
            )
            .add_field(name="Genres", value=genres, inline=True)
            .add_field(name="Themes", value=themes, inline=True)
            .add_field(
                name="Season/Year",
                value=f"`{season.capitalize() + " " + str(year) if season and year else "N/A"}`",
                inline=True,
            ),
            # Clue #2: Eps, Score, Ranked
            Embed(
                title="Clue #2: Do some stats help?",
                color=Color.red(),
                description=description,
            )
            .add_field(name="Episodes", value=f"`{episodes}` episodes", inline=True)
            .add_field(name="Score", value=score, inline=True)
            .add_field(name=f"Ranked: `{ranked}`", value="", inline=True),
            # Clue #3: Studio, Producers
            Embed(
                title="Clue #3: Who created this!?",
                color=Color.orange(),
                description=description,
            )
            .add_field(name="Studios", value=studios)
            .add_field(name="Producers", value=producers),
            # Clue #4: Synopsis
            Embed(
                title="Clue #4: You should recognize this",
                color=Color.green(),
                description=description,
            ).add_field(name="Summarized synopsis", value=synopsis_clue),
            # Clue #5: Image Cover
            Embed(
                title="Clue #5: Okay...",
                color=Color.green(),
                description=description,
            ).set_image(url="attachment://blurred.png"),
        ]

    def get_current_embed(self) -> Embed:
        return CluesClass.clues_embed[self.crr_clue_idx]

    def next_clue(self):
        self.crr_clue_idx += 1
        self.timer = CluesClass.clues_reveal_after[self.crr_clue_idx]

    def is_last_clue(self):
        return self.crr_clue_idx == len(CluesClass.clues_embed) - 1
