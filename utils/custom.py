from __future__ import annotations
from discord import ApplicationContext, Embed, Color, Member
from discord.ui import View
from dotmap import DotMap
from typing import List, Callable, Optional
import asyncio
import random
import time

# global tmp var from minigames.py
from utils.game_state import minigame_objects, players_games


async def count_down_timer(ctx: ApplicationContext,
                           timeout: int, *, 
                           title_prefix: str = "Time Left:", 
                           interval: int = 5, 
                           check_done: Optional[Callable] = None):

  timer_msg = await ctx.send(embed=Embed(title=f"{title_prefix} {timeout} seconds", color=Color.dark_magenta()))
  while timeout > 0:
    await asyncio.sleep(1) # ping every 1s
    timeout -= 1

    if timeout == 0:
      await timer_msg.delete()
    elif timeout % interval == 0 or timeout <= 5:
      await timer_msg.edit(embed=Embed(title=f"{title_prefix} {timeout} seconds", color=Color.dark_magenta()))

    if check_done and check_done():
      if timeout > 0:
        await timer_msg.delete()
      break
 

class CycleClass():
  # time limit in seconds
  join_timeout = 10
  pick_timeout = 60
  turn_timeout = 10

  phases = ["lobby", "picking", "turns"] 

  def __init__(self):
    minigame_objects.append(self) 

    self.players: List[Member] = []
    self.targets: dict[Member, Member] = {}
    self.given_by: dict[Member, Member] = {}
    self.player_animes: dict[Member, DotMap] = {}
    self.player_count = 0

    self.just_answered = False
    self.active_player_index = 0
    self.phase_index = 0 
    self.round = 1
    self.done_players: List[Member] = []
  
  def add_player(self, player: Member):
    self.player_count += 1
    self.players.append(player)
    players_games[player] = self # store which game the player is in

  # shuffle and find derangements of players, then assigned players to each other
  def random_pairs(self):
    random.shuffle(self.players)
    pairs = [i for i in range(self.player_count)]

    # Expected time complexity: ~ O(n)*e
    while True:
      random.shuffle(pairs)
      if all(pairs[i] != i for i in range(len(pairs))):
        break
    
    for idx, player in enumerate(self.players):
      self.targets[player] = self.players[pairs[idx]]
      self.given_by[self.players[pairs[idx]]] = player
  
  def current_player(self) -> Member:
    return self.players[self.active_player_index]

  def advance_player(self):
    self.active_player_index += 1
    self.active_player_index %= self.player_count

    if self.active_player_index == 0: 
      self.round += 1
  
  def add_done(self, player: Member):
    self.done_players.append(player)
  
  def advance_phase(self):
    self.phase_index += 1

  def current_phase(self) -> str:
    return CycleClass.phases[self.phase_index]
  
  def leaderboard(self) -> Embed:
    description = ""
    for rank, player in enumerate(self.done_players, start=1):
      anime = self.player_animes[player]
      giver = self.given_by[player]
      description += f"**#{rank}**: {player.mention} ❮❮ [{anime.title}]({anime.url}) ❮❮ {giver.mention}" 

    if not description: 
      description = "No one's here..."
    return Embed(
      title=".⋅˚₊‧ 🜲Leaderboard ‧₊˚ ⋅",
      description=description,
      color=Color.gold()
    )

  def clean_up(self):
    for player in self.players:
      if player in players_games:
        players_games.pop(player, None)

    if self in minigame_objects:
      minigame_objects.remove(self)