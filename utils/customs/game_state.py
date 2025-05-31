from typing import List, TYPE_CHECKING
from discord import Member

if TYPE_CHECKING:
    from .classes import CycleClass

# shared game states
minigame_objects: List["CycleClass"] = []
players_games: dict[Member, "CycleClass"] = {}
