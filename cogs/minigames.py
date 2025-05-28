import discord
from discord.ext import commands
from credentials import TEST_GUILD_ID, FRIEND_TEST_GUILD_ID
import random
import asyncio

from utils.jikanv4 import get_anime_by_id

guild_ids = [TEST_GUILD_ID]

cycle_game_list = [] # global temporary list for cycle games
players_games = {} # global temporary dictionary for players and their games


class cycleGame():
  def __init__(self):
    self.players = []
    self.assigned_mal_ids = {}
    self.pairs = []
    self.current_player_index = 0

  def add_player(self, player):
    # if player not in self.players:
    self.players.append(player)
    players_games[player] = self # Store the game for the player

  # find derangement of a list
  def random_pairs(self):
    self.pairs = [i for i in range(len(self.players))]
    # Expected time complexity: ~ O(n)*e
    while True:
      random.shuffle(self.pairs)
      if all(self.pairs[i] != i for i in range(len(self.pairs))):
        break

  def next_player(self):
    self.current_player_index = (self.current_player_index + 1) % len(self.players)
    return self.players[self.current_player_index]
  
  def clean_up(self):
    # clean up the game 
    for player in self.players:
      players_games.pop(player, None)

    if self in cycle_game_list:
      cycle_game_list.remove(self)
    

class JoinGame(discord.ui.View): 

  def __init__(self, cycle_object, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.cycle_object = cycle_object

  @discord.ui.button(label="click to join", style=discord.ButtonStyle.green, emoji="🤓") 
  async def button_callback(self, button, interaction):
    member = interaction.user
    if(member in self.cycle_object.players):
      await interaction.response.send_message(f"{member.mention}: You are already in the game!", ephemeral=True)
      return

    self.cycle_object.add_player(member)
    await interaction.response.send_message(f"{member.mention} joined!")


class MiniGames(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot
  
  cycle = discord.SlashCommandGroup("cycle", "cycle game commands")

  @cycle.command(guild_ids=guild_ids, description="Start an anime cycle game")
  async def start(self, ctx):
    """
    This game will assign each player a another random player.
    Everyone will pick an anime for their assigned player.
    After picking, every player will know the assigned anime of other players except their own.
    Each player will then take turns to ask for a hint from other players about the anime they was assigned to.
    Who knows the anime first wins!
    """

    cycle_object = cycleGame()
    cycle_game_list.append(cycle_object)

    view = JoinGame(cycle_object, timeout=5, disable_on_timeout=True)
    await ctx.respond(
      embed=discord.Embed(title="Anime Cycle has been started!", color=discord.Color.green()), 
      view=view
    )

    await view.wait()

    # TEST Variable
    # cycle_object.add_player(ctx.author)
    # cycle_object.add_player(self.bot.user)
    # cycle_object.assigned_mal_ids[0] = 9776

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

    # assigned players for every players
    cycle_object.random_pairs()

    await ctx.send(
      embed=discord.Embed(
        title="Lobby",
        description=f"Players: {', '.join([player.mention for player in cycle_object.players])}",
        color=discord.Color.blue()
      )
    )

    for i, player in enumerate(cycle_object.players):
      assigned_player = cycle_object.players[cycle_object.pairs[i]]
      await player.send(
        embed=discord.Embed(
          description=f"**{player.mention}**, you are assigned to **{assigned_player.mention}!**",
        )
      )
    
    await ctx.send("Pairing has been sent to each player via DM.")

    # each players pick an anime for their assigned player using /pick command
    await ctx.send(
      embed=discord.Embed(
        title="use `/cycle pick <anime_id>` command to pick an anime for your assigned player",
        description="You must find an anime id on [MyAnimeList](https://myanimelist.net/) only",
        color=discord.Color.yellow()
      )
    )

    timer = 10
    while len(cycle_object.assigned_mal_ids) < len(cycle_object.players):
      await asyncio.sleep(1)  # ping every 1s
      timer -= 1
      if timer == 0:
        await ctx.send(
          embed=discord.Embed(
            title="Anime Cycle game cancelled",
            description="Not all players picked an anime in time.",
            color=discord.Color.red()
          )
        )
        cycle_object.clean_up()
        return 
    

    
    cycle_object.clean_up()
  
  @cycle.command(guild_ids=guild_ids, description="Pick an anime for your assigned player")
  async def pick(self, ctx, anime_id: int):
    """
    Pick an anime for assigned player using MAL anime id.
    """
    member = ctx.author
    cycle_object = players_games.get(member)

    if not cycle_object:
      await ctx.respond(f"{member.mention}: You are not in any anime cycle game.", ephemeral=True)
      return

    result = await get_anime_by_id(anime_id)
    if not result:
      await ctx.respond(f"{member.mention} invalid anime id provided.", ephemeral=True)
      return
    
    title = result.data.title
    url = result.data.url
    
    pair = cycle_object.pairs[cycle_object.players.index(member)] # get index of assigned player
    pair_member = cycle_object.players[pair] # get member object of assigned player

    cycle_object.assigned_mal_ids[pair] = result.data.mal_id
    await ctx.respond(f"{ctx.author.mention}: You picked [{title}]({url}) for {pair_member.mention}!", ephemeral=True)
  
  @cycle.command(guild_ids=guild_ids, description="Submit your answer here!")
  async def answer(self, ctx, anime_id: int):
    """
    Submit your answer here!
    If you are correct, you will win the game.
    """
    member = ctx.author
    cycle_object = players_games.get(member)

    if not cycle_object:
      await ctx.respond(f"{member.mention}: You are not in any anime cycle game.", ephemeral=True)
      return

    idx = cycle_object.players.index(member)
    if idx != cycle_object.current_player_index:
      await ctx.respond(f"{member.mention}: It's not your turn yet!", ephemeral=True)
      return

    assigned_mal_id = cycle_object.assigned_mal_ids[idx]

    result = await get_anime_by_id(anime_id)
    if not result:
      await ctx.respond(f"{member.mention} invalid anime id provided.", ephemeral=True)
      return

    title = result.data.title
    url = result.data.url
    mal_id = result.data.mal_id

    if assigned_mal_id == mal_id:
      await ctx.respond(f"{member.author.mention} You guessed it right! The anime is [{title}]({url})", ephemeral=True)
      cycle_object.clean_up()
      return

    await ctx.respond(f"{ctx.author.mention} Wrong answer! Try again...", ephemeral=True)



def setup(bot):
  bot.add_cog(MiniGames(bot))
