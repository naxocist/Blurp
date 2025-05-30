from typing import List
from dotmap import DotMap

import discord
from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Interaction
from discord.ui import View, Button

import random
import asyncio
from utils.jikanv4 import get_anime_by_id
from credentials import guild_ids

# global tmp running game info 
minigame_objects = [] 
players_games = {} 


class CycleClass():
  # time limit in seconds
  join_timeout = 10
  pick_timeout = 600
  turn_timeout = 60

  phases = ["lobby", "picking", "turns"] 

  def __init__(self):
    minigame_objects.append(self) 

    self.players: List[Member] = []
    self.targets: dict[Member, Member] = {}
    self.player_animes: dict[Member, DotMap] = {}
    self.player_count = 0

    self.active_player_index = 0
    self.phase_index = 0 
    self.round = 0
    self.done_players: List[Member] = []
  
  def add_player(self, player):
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
  
  def current_player(self):
    return self.players[self.active_player_index]

  def advance_player(self):
    if self.active_player_index == 0: 
      self.round += 1
    self.active_player_index = (self.active_player_index + 1) % self.player_count
  
  def add_done(self, player: Member):
    self.done_players.append(player)
  
  def advance_phase(self):
    self.phase_index += 1

  def current_phase(self):
    return CycleClass.phases[self.phase_index]
  
  def leaderboard(self) -> Embed:
    return Embed(
      title="Leaderboard",
      description="\n".join([f"**#{rank}**: {player.mention}" for rank, player in enumerate(self.done_players, start=1)]),
      color=discord.Colour.gold()
    )

  def clean_up(self):
    for player in self.players:
      if player in players_games:
        players_games.pop(player, None)

    if self in minigame_objects:
      minigame_objects.remove(self)
    

class MiniGames(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot
  
  cycle = discord.SlashCommandGroup("cycle", "cycle game commands", guild_ids=guild_ids)

  @cycle.command(description="Start an anime cycle game")
  async def start(self, ctx: ApplicationContext):
    """
    This game will assign each player a another random player.
    Everyone will pick an anime for their assigned player.
    After picking, every player will know the assigned anime of other players except their own.
    Each player will then take turns to ask for a hint from other players about the anime they was assigned to.
    Who knows the anime first wins!
    """

    await ctx.defer()

    cycle_object = CycleClass()

    invite_view = View(timeout=CycleClass.join_timeout, disable_on_timeout=True)
    join_button = Button(label="click to join", style=discord.ButtonStyle.primary, emoji="🤓")
    start_button = Button(label="click to start", style=discord.ButtonStyle.green, emoji="💀")

    async def join_callback(interaction: Interaction):
      nonlocal cycle_object

      member: Member = interaction.user
      if member in cycle_object.players:
        await interaction.response.send_message(f"You are already in the game!", ephemeral=True)
        return

      cycle_object.add_player(member)
      await interaction.response.send_message(f"{member.mention} joined!")
    
    async def start_callback(interaction: Interaction):
      invite_view.stop()
      invite_view.disable_all_items()
      await interaction.response.edit_message(view=invite_view)
    
    join_button.callback = join_callback
    start_button.callback = start_callback
    invite_view.add_item(join_button)
    invite_view.add_item(start_button)

    await ctx.respond(
      embed=Embed(title="Anime Cycle has been started!", color=Color.green()), 
      view=invite_view
    )

    await invite_view.wait()

    # DEMO player
    # cycle_object.add_player(ctx.author)
    # cycle_object.add_player(self.bot.user)
    # cycle_object.assigned_animes[ctx.author] = DotMap(dict(title="TEST", url="TEST.com", mal_id=9337))

    # too few players to start the game
    if cycle_object.player_count < 2:
      await ctx.send(
        embed=Embed(
          title="Anime Cycle game cancelled",
          description="Too few players to start the game.",
          color=Color.red()
        ),
      )
      cycle_object.clean_up()
      return

    # LOBBY
    await ctx.send(
      embed=Embed(
        title=f"Lobby: {cycle_object.player_count} players",
        description=', '.join([player.mention for player in cycle_object.players]),
        color=Color.blue()
      )
    )

    # assign every player another player
    cycle_object.random_pairs()

    # notify players about their assigned player via DM
    for player in cycle_object.players:
      target = cycle_object.targets[player]
      await player.send(embed=Embed(
        description=f"You need to pick an anime for **{target.mention}!**",
        color=Color.purple(),
      ))

    await ctx.send(embed=Embed(
      title="Pairing has been sent to every player via DM.", 
      color=Color.brand_green())
    )

    # PICKING: each players pick an anime for their assigned player using /pick command
    cycle_object.advance_phase()
    await ctx.send(
      embed=Embed(
        title="use `/cycle pick <anime_id>` command to pick an anime for your assigned player",
        description="You must find an anime id on [MyAnimeList](https://myanimelist.net/) only\nExample: https://myanimelist.net/anime/9776/A-Channel\n**9776** is the anime id",
        color=Color.yellow()
      )
    )

    timer = CycleClass.pick_timeout
    while timer > 0:
      await asyncio.sleep(1) # ping every 1s
      timer -= 1
      if len(cycle_object.player_animes) == cycle_object.player_count:
        break

    # someone didn't pick an anime in time
    if len(cycle_object.player_animes) < cycle_object.player_count:
      await ctx.send(
        embed=Embed(
          title="Anime Cycle game cancelled",
          description="Not all players picked an anime in time.",
          color=Color.red()
        )
      )
      cycle_object.clean_up()
      return 
    
    # notify every player about other players' assigned anime
    for player in cycle_object.players:
      info = ""
      for plyr in cycle_object.players:
        if plyr == player:
          continue 
        assigned_anime = cycle_object.player_animes[plyr]
        info += f"{plyr.mention}: [{assigned_anime.title}]({assigned_anime.url})\n"

      await player.send(embed=Embed(
        title="Information",
        description=info,
        colour=Color.blurple()
      ))

    # 5 seconds delay
    await asyncio.sleep(5)

    # Now the game starts, each player will take turns to get hints or take a guess about their assigned anime
    cycle_object.advance_phase()
    while len(cycle_object.done_players) < cycle_object.player_count:
      current_player = cycle_object.current_player()

      if current_player in cycle_object.done_players:
        cycle_object.advance_player()
        continue

      turn_view = View(timeout=CycleClass.turn_timeout, disable_on_timeout=True)
      continue_button = Button(label="next player", style=discord.ButtonStyle.green)
      terminate_button = Button(label="terminate", style=discord.ButtonStyle.red)

      is_terminate = False
      terminator: Member = None

      async def continue_callback(interaction: Interaction):
        nonlocal turn_view
        turn_view.stop()
        await interaction.response.defer() 

      async def terminate_callback(interaction: Interaction):
        nonlocal is_terminate, terminator
        await interaction.response.defer()
        is_terminate = True
        terminator = interaction.user
        turn_view.stop()
        return 

      continue_button.callback = continue_callback
      terminate_button.callback = terminate_callback
      turn_view.add_item(continue_button)
      turn_view.add_item(terminate_button)

      message = await ctx.send(embed=Embed(
        title=f"Round :{cycle_object.round}",
        description=f"{current_player.mention}'s turn! Go ahead and ask for some hints.\nWhen you're ready, use `/cycle answer <anime_id>` to submit your answer.",
        color=Color.purple(),
      ),
        view=turn_view
      )

      await turn_view.wait()

      if turn_view.is_finished():
        cycle_object.advance_player()
        turn_view.disable_all_items()
        await message.edit(view=turn_view)

        # Early terminate by a member
        if is_terminate:
          await ctx.send(embed=Embed(
            description=f"**{terminator.mention} terminated the game...**",
            color=Color.red()
          ))
          cycle_object.clean_up()
          return 

    
    await ctx.send("Anime Cycle Ended!")
    cycle_object.clean_up()
  
  # This command should be used in "picking" phase
  @cycle.command(description="Pick an anime for your assigned player")
  async def pick(self, ctx: ApplicationContext, anime_id: int):
    """
    Pick an anime for assigned player using MAL anime id.
    """
    member: Member = ctx.author
    cycle_object: CycleClass = players_games.get(member)

    if not cycle_object:
      await ctx.respond(f"You are not in any anime cycle game.", ephemeral=True)
      return
    
    if cycle_object.current_phase() != "picking":
      await ctx.respond(f"The game is not in the picking phase yet!", ephemeral=True)
      return

    result = await get_anime_by_id(anime_id)
    if not result:
      await ctx.respond(f"Invalid anime id was provided.", ephemeral=True)
      return
    
    title, url, mal_id= result.data.title, result.data.url, result.data.mal_id

    target: Member = cycle_object.targets[member] # get member object of assigned player

    # assigned that player a dotmapped compact anime info
    cycle_object.player_animes[target] = DotMap(dict(title=title, url=url, mal_id=mal_id))

    await ctx.respond(f"You picked [{title}]({url}) for {target.mention}!", ephemeral=True)

    req: int = len(cycle_object.player_animes) - cycle_object.player_count
    if req > 0: 
      await ctx.send(embed=Embed(description=f"There are {req} players who still need to pick an anime.", color=Color.yellow()))
    
  
  # This command should be used in "turns" phase
  @cycle.command(description="Submit your answer here!")
  async def answer(self, ctx: ApplicationContext, anime_id: int):
    """
    Member will use this command to submit their answer
    """
    member: Member = ctx.author
    cycle_object: CycleClass = players_games.get(member)

    if not cycle_object:
      await ctx.respond(f"You are not in any anime cycle game.", ephemeral=True)
      return

    if cycle_object.current_phase() != "turns":
      await ctx.respond(f"The game is not in the turns phase yet!", ephemeral=True)
      return

    if member != cycle_object.current_player():
      await ctx.respond(f"It's not your turn yet!", ephemeral=True)
      return

    result = await get_anime_by_id(anime_id)
    if not result:
      await ctx.respond(f"Invalid anime id was provided.", ephemeral=True)
      return

    title, url, mal_id = result.data.title, result.data.url, result.data.mal_id

    target: DotMap = cycle_object.player_animes[member] # retrieve player's assigned anime

    guessed = f"{member.mention} guessed [{title}]({url})\n" 
    embed = None
    if target.mal_id == mal_id:
      guessed += "Correct!"
      cycle_object.add_done(member)
      embed=cycle_object.leaderboard()
    else:
      guessed += "Not quite right... Try again!"

    await ctx.respond(guessed, embed)
    


def setup(bot):
  bot.add_cog(MiniGames(bot))
