from __future__ import annotations

from typing import TYPE_CHECKING

from discord import Member

if TYPE_CHECKING:
    from utils.customs.components.aniclues_comps import CluesClass
    from utils.customs.components.anicycle_comps import CycleClass

# shared game states
minigame_objects: list[CycleClass | CluesClass] = []
players_games: dict[Member, CycleClass | CluesClass] = {}
