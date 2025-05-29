import discord
from discord.ext import commands
import random
import asyncio

from utils.jikanv4 import get_anime_by_id

from credentials import guild_ids

minigame_objects = [] # global temporary list for minigame objects
players_games = {} # global temporary dictionary for players and their games


class CycleClass():
  join_timeout = 10 # seconds to join the game
  pick_timeout = 10 # seconds to pick an anime
  turn_timeout = 10 # seconds to take a turn
  phase = "lobby" # current phase of the game, can be "lobby", "picking", "turns"

  def __init__(self):
    minigame_objects.append(self) # add this object to the global list
    self.players = []
    self.assigned_mal_ids = {}
    self.assigned_players = {}
    self.current_player_index = 0
    self.done = []

  # add player to the game
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
  def done(self, player):
    self.done.append(player)
  
  # clean up the game 
  def clean_up(self):
    for player in self.players:
      players_games.pop(player, None)

    if self in minigame_objects:
      minigame_objects.remove(self)
    

class MiniGames(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot
  
  cycle = discord.SlashCommandGroup("cycle", "cycle game commands", guild_ids=guild_ids)

  @cycle.command(description="Start an anime cycle game")
  async def start(self, ctx):
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
        await interaction.response.send_message(f"{member.mention}: You are already in the game!", ephemeral=True)
        return

      cycle_object.add_player(member)
      await interaction.response.send_message(f"{member.mention} joined!")
      
    start_button.callback = start_callback
    start_view.add_item(start_button)

    await ctx.respond(
      embed=discord.Embed(title="Anime Cycle has been started!", color=discord.Color.green()), 
      view=start_view
    )

    # wait for players to join the game
    await start_view.wait()

    # TEST Variable
    cycle_object.add_player(ctx.author)
    cycle_object.add_player(self.bot.user)
    cycle_object.assigned_mal_ids[ctx.author] = 9776

    # too few players to start the game
    if len(cycle_object.players) < 2:
      await ctx.send(
        embed=discord.Embed(
          title="Anime Cycle game cancelled",
          description="Too few players to start the game.",
          color=discord.Color.red()
        )
      )
      cycle_object.clean_up()
      return

    # show lobby status
    await ctx.send(
      embed=discord.Embed(
        title="Lobby",
        description=f"Players: {', '.join([player.mention for player in cycle_object.players])}",
        color=discord.Color.blue()
      )
    )

    # gives assigned players to every players
    cycle_object.random_pairs()

    # notify players about their assigned player via DM
    # for player in cycle_object.players:
    #   assigned_player = cycle_object.assigned_players[player]
    #   await player.send(
    #     embed=discord.Embed(
    #       description=f"You need to pick an anime for **{assigned_player.mention}!**",
    #       color=discord.Color.purple()
    #     )
    #   )
    await ctx.send(embed=discord.Embed(description="Pairing has been sent to every player via DM."))

    # each players pick an anime for their assigned player using /pick command
    cycle_object.phase = "picking"
    await ctx.send(
      embed=discord.Embed(
        title="use `/cycle pick <anime_id>` command to pick an anime for your assigned player",
        description="You must find an anime id on [MyAnimeList](https://myanimelist.net/) only\nExample: https://myanimelist.net/anime/9776/A-Channel\n**9776** is the anime id",
        color=discord.Color.yellow()
      )
    )

    timer = CycleClass.pick_timeout
    while timer > 0:
      await asyncio.sleep(1)  # ping every 1s
      timer -= 1
      if len(cycle_object.assigned_mal_ids) == len(cycle_object.players):
        break

    # someone didn't pick an anime in time
    if len(cycle_object.assigned_mal_ids) < len(cycle_object.players):
      await ctx.send(
        embed=discord.Embed(
          title="Anime Cycle game cancelled",
          description="Not all players picked an anime in time.",
          color=discord.Color.red()
        )
      )
      cycle_object.clean_up()
      return 
    

    # Now the game starts, each player will take turns to get hints or take a guess about their assigned anime
    cycle_object.phase = "turns"
    while len(cycle_object.done) < len(cycle_object.players):
      continue_view = discord.ui.View(timeout=CycleClass.turn_timeout, disable_on_timeout=True)
      continue_button = discord.ui.Button(
        label="next", 
        style=discord.ButtonStyle.green, 
      )

      async def continue_callback(interaction):
        nonlocal continue_view
        continue_view.stop()
        await interaction.response.defer() 

      continue_button.callback = continue_callback
      continue_view.add_item(continue_button)

      current_player = cycle_object.current_player()
      if current_player in cycle_object.done:
        cycle_object.advance()
        continue

      message = await ctx.send(
        embed=discord.Embed(
          description=f"{current_player.mention}'s turn! Ask for some hints.\n If you're ready, use `/cycle answer <anime_id>` to submit your answer.",
          color=discord.Color.purple(),
        ),
        view=continue_view
      )

      await continue_view.wait()
      if continue_view.is_finished():
        cycle_object.advance()
        continue_view.disable_all_items()
        await message.edit(view=continue_view)

    
    await ctx.send(
      embed=discord.Embed(
        title="Anime Cycle terminated!",
        color=discord.Color.green(),
      )
    )

    cycle_object.clean_up()
  
  # This command should be used in "picking" phase
  @cycle.command(description="Pick an anime for your assigned player")
  async def pick(self, ctx, anime_id: int):
    """
    Pick an anime for assigned player using MAL anime id.
    """
    member = ctx.author
    cycle_object = players_games.get(member)

    if not cycle_object:
      await ctx.respond(f"You are not in any anime cycle game.", ephemeral=True)
      return
    
    if cycle_object.phase != "picking":
      await ctx.respond(f"The game is not in the picking phase yet!", ephemeral=True)
      return

    result = await get_anime_by_id(anime_id)
    if not result:
      await ctx.respond(f"Invalid anime id was provided.", ephemeral=True)
      return
    
    title = result.data.title
    url = result.data.url
    mal_id = result.data.mal_id
    
    assigned_player = cycle_object.assigned_players[member] # get member object of assigned player

    cycle_object.assigned_mal_ids[assigned_player] = mal_id
    await ctx.respond(f"{member.mention}: You picked [{title}]({url}) for {assigned_player.mention}!", ephemeral=True)

    req = len(cycle_object.assigned_mal_ids) - len(cycle_object.players)
    if req > 0: 
      await ctx.send(embed=discord.Embed(description=f"There are {req} players who still need to pick an anime.", color=discord.Color.yellow()))
    
  
  # This command should be used in "turns" phase
  @cycle.command(description="Submit your answer here!")
  async def answer(self, ctx, anime_id: int):
    """
    Submit your answer here!
    If you are correct, you will win the game.
    """
    member = ctx.author
    cycle_object = players_games.get(member)

    if not cycle_object:
      await ctx.respond(f"You are not in any anime cycle game.", ephemeral=True)
      return

    if cycle_object.phase != "turns":
      await ctx.respond(f"The game is not in the turns phase yet!", ephemeral=True)
      return

    if member != cycle_object.current_player():
      await ctx.respond(f"It's not your turn yet!", ephemeral=True)
      return


    result = await get_anime_by_id(anime_id)
    if not result:
      await ctx.respond(f"Invalid anime id was provided.", ephemeral=True)
      return

    title = result.data.title
    url = result.data.url
    mal_id = result.data.mal_id

    assigned_mal_id = cycle_object.assigned_mal_ids[member]
    if assigned_mal_id == mal_id:
      await ctx.respond(f"{member.mention} guessed it right! {member.mention}'s assigned anime is [{title}]({url})")
      cycle_object.done(member)
      return

    await ctx.respond(f"{member.mention} Wrong answer! Try again...", ephemeral=True)



def setup(bot):
  bot.add_cog(MiniGames(bot))
