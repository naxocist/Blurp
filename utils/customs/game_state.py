from __future__ import annotations
from typing import List, TYPE_CHECKING
from discord import Member

if TYPE_CHECKING:
    from .anicycle_comps import CycleClass
    from .aniclues_comps import CluesClass

# shared game states
minigame_objects: List[CycleClass | CluesClass] = []
players_games: dict[Member, CycleClass | CluesClass] = {}
