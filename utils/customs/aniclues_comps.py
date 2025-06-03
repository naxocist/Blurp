from dotmap import DotMap
from discord import Embed

from typing import List
from bisect import bisect_right


class CluesClass:
    clues_embed = []
    clues_reveal_after: List[int] = [0, 5, 5, 5]
    delay = 20
    timer = sum(clues_reveal_after) + delay

    def __init__(self, anime: DotMap):
        self.crr_clue_idx: int = 0
        self.anime = anime

        CluesClass.clues_embed = [
            Embed(title="Clue #1"),
            Embed(title="Clue #2"),
            Embed(title="Clue #3"),
            Embed(title="Clue #4"),
        ]
        # synopsis_clue = await get_synopsis_clue(anime)
        # genres = " ".join(f"`{genre.name}`" for genre in anime.genres)

        self.pref_clues_reveal_after: List[int] = []
        for i, clue_reveal_after in enumerate(CluesClass.clues_reveal_after):
            pref = clue_reveal_after
            if i > 0:
                pref += self.pref_clues_reveal_after[i - 1]

            self.pref_clues_reveal_after.append(pref)

    def get_new_clue_embed(self, timer: int):
        time_passed = CluesClass.timer - timer

        nxt_clue_idx = bisect_right(self.pref_clues_reveal_after, time_passed) - 1
        print(time_passed, nxt_clue_idx)
        if nxt_clue_idx == -1 or nxt_clue_idx == self.crr_clue_idx:
            return CluesClass.clues_embed[self.crr_clue_idx]

        return CluesClass.clues_embed[nxt_clue_idx]
