from dotmap import DotMap
from discord import Embed

from typing import List
import asyncio

from utils.apis.typhoon import get_synopsis_clue


class CluesClass:
    clues_embed = []
    clues_reveal_after: List[int] = [0, 10, 5, 10]
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
        themes = " ".join(f"`{theme.name}`" for theme in anime.themes) or "N/A"
        status = anime.status or "N/A"
        season = anime.season
        year = anime.year
        episodes = anime.episodes or "N/A"
        score = f"`{anime.score}`/10" or "`N/A`"
        ranked = f"#{anime.rank}" or "N/A"

        CluesClass.clues_embed = [
            Embed(title="Clue #1")
            .add_field(name="Genres", value=genres, inline=True)
            .add_field(name="Themes", value=themes)
            .add_field(name="Status", value=status, inline=True)
            .add_field(
                name="Season | Year",
                value=f"`{season.capitalize() + " " + str(year) if season and year else "N/A"}`",
            ),
            Embed(title="Clue #2"),
            Embed(title="Clue #3"),
            Embed(title="Clue #4"),
        ]

        self.answered_event = asyncio.Event()

    async def get_synopsis_clue(self):
        synopsis_clue = await get_synopsis_clue(self.anime)
        CluesClass.clues_embed[1].add_field(name="Synopsis", value=synopsis_clue)

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
