from dotmap import DotMap
from discord import Embed

from typing import List


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

        CluesClass.clues_embed = [
            Embed(title="Clue #1"),
            Embed(title="Clue #2"),
            Embed(title="Clue #3"),
            Embed(title="Clue #4"),
        ]
        # synopsis_clue = await get_synopsis_clue(anime)
        # genres = " ".join(f"`{genre.name}`" for genre in anime.genres)

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

    def skip_clue(self, timer: int):
        self.skip = True
