from typing import List
from dotmap import DotMap

import discord
from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Interaction

import random
import asyncio
from utils.jikanv4 import get_anime_by_id
from credentials import guild_ids

# global tmp game info 
minigame_objects = [] # what game is currently running
players_games = {} # what game a player belongs to


class CycleClass():
  # time limit in seconds
  join_timeout = 10
  pick_timeout = 600
  turn_timeout = 60

  # phases in this game
  phases = ["lobby", "picking", "turns"] 

  def __init__(self):
    # add this cycle object to the global tmp storage
    minigame_objects.append(self) 

    self.players: List[Member] = []
    self.assigned_players: dict[Member, Member] = {}
    self.assigned_animes: dict[Member, DotMap] = {} # { Member: dotmapped compact anime info }
    self.current_player_index = 0
    self.current_phase_index = 0 
    self.done: List[Member] = []
  
  # add a player to the game
  def add_player(self, player):
    self.players.append(player)
    players_games[player] = self # store which game the player is in

  # shuffle and find derangements of players, then assigned players to each other
  def random_pairs(self):
    random.shuffle(self.players)
    pairs = [i for i in range(len(self.players))]

    # Expected time complexity: ~ O(n)*e
    while True:
      random.shuffle(pairs)
      if all(pairs[i] != i for i in range(len(pairs))):
        break
    
    for idx, player in enumerate(self.players):
      self.assigned_players[player] = self.players[pairs[idx]]
  
  # get current player member object
  def current_player(self):
    return self.players[self.current_player_index]

  # advance to the next player
  def advance(self):
    self.current_player_index = (self.current_player_index + 1) % len(self.players)
  
  # mark player who answered correctly
  def add_done(self, player: Member):
    self.done.append(player)
  
  # advance to the next phase
  def advance_phase(self):
    self.current_phase_index += 1

  # return current phase name
  def current_phase(self):
    return CycleClass.phases[self.current_phase_index]
  
  def leaderboard(self) -> Embed:
    return Embed(
      title="Leaderboard",
      description="\n".join([f"#{rank}: {player.mention}" for rank, player in enumerate(self.done, start=1)]),
      color=discord.Colour.gold()
    )

  # clean up the game 
  def clean_up(self):
    for player in self.players:
      if player in players_games:
        players_games.pop(player, None)

    if self in minigame_objects:
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

    start_view = discord.ui.View(timeout=CycleClass.join_timeout, disable_on_timeout=True)
    start_button = discord.ui.Button( label="click to join", style=discord.ButtonStyle.green, emoji="🤓")

    async def start_callback(interaction):
      nonlocal cycle_object

      member = interaction.user
      if member in cycle_object.players:
        await interaction.response.send_message(f"You are already in the game!", ephemeral=True)
        return

      cycle_object.add_player(member)
      await interaction.response.send_message(f"{member.mention} joined!")
      
    start_button.callback = start_callback
    start_view.add_item(start_button)

    await ctx.respond(
      embed=Embed(title="Anime Cycle has been started!", color=Color.green()), 
      view=start_view
    )

    # wait for players to join the game
    await start_view.wait()

    # DEMO player
    # cycle_object.add_player(ctx.author)
    # cycle_object.add_player(self.bot.user)
    # cycle_object.assigned_animes[ctx.author] = DotMap(dict(title="TEST", url="TEST.com", mal_id=9337))

    # too few players to start the game
    if len(cycle_object.players) < 2:
      await ctx.send(
        embed=Embed(
          title="Anime Cycle game cancelled",
          description="Too few players to start the game.",
          color=Color.red()
        )
      )
      cycle_object.clean_up()
      return

    # LOBBY
    await ctx.send(
      embed=Embed(
        title=f"Lobby: {len(cycle_object.players)} players",
        description=', '.join([player.mention for player in cycle_object.players]),
        color=Color.blue()
      )
    )

    # assign every player another player
    cycle_object.random_pairs()

    # notify players about their assigned player via DM
    for player in cycle_object.players:
      assigned_player = cycle_object.assigned_players[player]
      await player.send(embed=Embed(
        description=f"You need to pick an anime for **{assigned_player.mention}!**",
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
      if len(cycle_object.assigned_animes) == len(cycle_object.players):
        break

    # someone didn't pick an anime in time
    if len(cycle_object.assigned_animes) < len(cycle_object.players):
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
      for p in cycle_object.players:
        if p == player:
          continue 
        assigned_anime = cycle_object.assigned_animes[p]
        info += f"{p.mention}: [{assigned_anime.title}]({assigned_anime.url})\n"

      await player.send(embed=Embed(
        title="Information",
        description=info,
        colour=Color.blurple()
      ))

    # 5 seconds delay
    await asyncio.sleep(5)

    # Now the game starts, each player will take turns to get hints or take a guess about their assigned anime
    cycle_object.advance_phase()
    cycle_object.phase = "turns"
    while len(cycle_object.done) < len(cycle_object.players):
      turn_view = discord.ui.View(timeout=CycleClass.turn_timeout, disable_on_timeout=True)
      continue_button = discord.ui.Button(label="next player", style=discord.ButtonStyle.green)
      terminate_button = discord.ui.Button(label="terminate", style=discord.ButtonStyle.red)

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

      current_player = cycle_object.current_player()
      if current_player in cycle_object.done:
        cycle_object.advance()
        continue

      message = await ctx.send(embed=Embed(
        description=f"{current_player.mention}'s turn! Go ahead and ask for some hints.\nWhen you're ready, use `/cycle answer <anime_id>` to submit your answer.",
        color=Color.purple(),
      ),
        view=turn_view
      )

      await turn_view.wait()
      if turn_view.is_finished():
        cycle_object.advance()
        turn_view.disable_all_items()
        await message.edit(view=turn_view)

        # Early terminate by a member
        if is_terminate:
          await ctx.send(embed=Embed(
            description=f"**{terminator.mention} terminated this game...**",
            color=Color.red()
          ))
          cycle_object.clean_up()
          return 

    
    await ctx.send("Anime Cycle Ended!", embed=cycle_object.leaderboard())
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

    assigned_player: Member = cycle_object.assigned_players[member] # get member object of assigned player

    # assigned that player a dotmapped compact anime info
    cycle_object.assigned_animes[assigned_player] = DotMap(dict(title=title, url=url, mal_id=mal_id))

    await ctx.respond(f"You picked [{title}]({url}) for {assigned_player.mention}!", ephemeral=True)

    req: int = len(cycle_object.assigned_animes) - len(cycle_object.players)
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

    assigned_anime: DotMap = cycle_object.assigned_animes[member] # retrieve player's assigned anime

    guessed = f"{member.mention} guessed [{title}]({url})\n" 
    if assigned_anime.mal_id == mal_id:
      guessed += "Correct!"
      cycle_object.add_done(member)
    else:
      guessed += "Not quite right... Try again!"

    
    await ctx.respond(guessed, embed=cycle_object.leaderboard())


def setup(bot):
  bot.add_cog(MiniGames(bot))
