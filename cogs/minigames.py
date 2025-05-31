from dotmap import DotMap
from typing import List

import discord
from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Interaction, Bot
from discord.ui import View, Button

import asyncio
from utils.jikanv4 import get_anime_by_id
from utils.nekosbest import get_img
from utils.custom import count_down_timer, CycleClass
from utils.game_state import players_games

from credentials import guild_ids


class MiniGames(commands.Cog):

  def __init__(self, bot): 
    self.bot: Bot = bot
  
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
    join_button = Button(label="join", style=discord.ButtonStyle.green, emoji="🤓")
    start_button = Button(label="force start", style=discord.ButtonStyle.blurple, emoji="💀")
    terminate_button = Button(label="terminate", style=discord.ButtonStyle.red)

    async def join_callback(interaction: Interaction):
      member: Member = interaction.user
      if member in cycle_object.players:
        await interaction.response.send_message(f"You are already in the game!", ephemeral=True)
        return

      cycle_object.add_player(member)
      await interaction.response.send_message(f"{member.mention} joined!")
    
    async def start_callback(interaction: Interaction):
      await interaction.response.defer()
      invite_view.stop()

    is_terminate = False
    terminator = None
    async def terminate_callback(interaction: Interaction):
      nonlocal is_terminate, terminator
      await interaction.response.defer()
      is_terminate = True
      terminator = interaction.user
      invite_view.stop()

    join_button.callback = join_callback
    start_button.callback = start_callback
    terminate_button.callback = terminate_callback
    invite_view.add_item(join_button)
    invite_view.add_item(start_button)
    invite_view.add_item(terminate_button)

    intro_msg = await ctx.respond(
      embed=Embed(title="Anime Cycle has been started!", color=Color.nitro_pink()),
      view=invite_view
    )

    await invite_view.wait()
    invite_view.disable_all_items()
    await intro_msg.edit(view=invite_view)

    if is_terminate:
      await ctx.send(embed=Embed(
        description=f"**{terminator.mention} terminated the game...**",
        color=Color.red()
      ))
      return 

    # DEMO player
    cycle_object.add_player(ctx.author)
    cycle_object.add_player(self.bot.user)
    cycle_object.player_animes[ctx.author] = DotMap(dict(title="Aharen-san wa Hakarenai Season 2", url="https://myanimelist.net/anime/59466/Aharen-san_wa_Hakarenai_Season_2", mal_id=59466))

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

    # assign every player another player
    cycle_object.random_pairs()

    # LOBBY & PAIRING STATUS
    players_list = ', '.join([player.mention for player in cycle_object.players])
    pairs_info = ""
    for player in cycle_object.players:
      target = cycle_object.targets[player]
      pairs_info += f"{player.mention} ➜ {target.mention}\n"

    await ctx.send(embed=Embed(
      title="Lobby", 
      description=players_list,
      thumbnail=(await get_img("thumbsup")).url,
      color=Color.brand_green()).add_field(name="Pairing", value=pairs_info)
    )

    # PICKING: each players pick an anime for their target using /pick command
    cycle_object.advance_phase()
    picking_msg = await ctx.send(
      embed=Embed(
        title="use `/cycle pick <anime_id>` to pick an anime for your pair",
        description="You must find an anime id on [MyAnimeList](https://myanimelist.net/) only\nExample: https://myanimelist.net/anime/9776/A-Channel\n`9776` is the anime id",
        color=Color.yellow()
      )
    )

    all_picked = lambda: len(cycle_object.player_animes) == cycle_object.player_count
    await count_down_timer(ctx, CycleClass.pick_timeout, check_done=all_picked)

    await picking_msg.delete()
    
    # someone didn't pick an anime in time
    if not all_picked:
      await ctx.send(
        embed=Embed(
          title="Anime Cycle game cancelled",
          description="Not all players picked an anime in time.",
          color=Color.red()
        )
      )
      cycle_object.clean_up()
      return 
    
    # DM everyone about assigned anime info
    for player in cycle_object.players:
      info = ""
      for plyr in cycle_object.players:
        if plyr == player:
          continue 
        assigned_anime = cycle_object.player_animes[plyr]
        info += f"{plyr.mention} ❮❮ [{assigned_anime.title}]({assigned_anime.url})\n"

      if player.bot: continue 
      await player.send(embed=Embed(
        title="Information",
        description=info,
        colour=Color.blurple()
      ))

    # after pick delay, let players look at the sent info
    await count_down_timer(ctx, cycle_object.delay_after_pick, title_prefix="Game Start In:")

    is_terminate = False
    terminator: Member = None

    # Turn View template
    def new_turn_view(is_last_player) -> View:
      nonlocal is_terminate, terminator
      turn_view = View()

      continue_button = Button(label="next player", style=discord.ButtonStyle.green, disabled=is_last_player)
      terminate_button.disabled = False

      is_terminate = False
      terminator = None

      async def continue_callback(interaction: Interaction):
        await interaction.response.defer()
        turn_view.stop()

      async def terminate_callback(interaction: Interaction):
        nonlocal is_terminate, terminator
        await interaction.response.defer()
        is_terminate = True
        terminator = interaction.user
        turn_view.stop()

      continue_button.callback = continue_callback
      terminate_button.callback = terminate_callback
      turn_view.add_item(continue_button)
      turn_view.add_item(terminate_button)

      return turn_view
      

    # Initial turn setup
    turn_msg = await ctx.send(
      embed=Embed(
        title=f"Round: {cycle_object.round} | Time Left: {cycle_object.turn_timeout} seconds",
        description=f"{cycle_object.current_player().mention}'s turn! Ask for some hints.\nWhen you're ready, use `/cycle answer <anime_id>` to submit your answer.",
        color=Color.purple(),
      ),
      view=new_turn_view(is_last_player=False)
    )

    leaderboard = await ctx.send(embed=cycle_object.leaderboard())

    # Now the game starts, each player will take turns to get hints or take a guess about their assigned anime
    cycle_object.advance_phase()
    while len(cycle_object.done_players) < cycle_object.player_count:
      player_left = cycle_object.player_count - len(cycle_object.done_players)
      current_player = cycle_object.current_player()

      if current_player in cycle_object.done_players:
        cycle_object.advance_player()
        continue

      is_last_player = player_left == 1
      turn_view = new_turn_view(is_last_player=is_last_player)

      timeout = cycle_object.turn_timeout
      while timeout > 0 and not turn_view.is_finished():
          
        await turn_msg.edit(
          embed=Embed(
            title=f"Round {cycle_object.round} | ⏱︎ Time left: {str(timeout) + " secs" if not is_last_player else "-"} | Players left: {player_left}",
            description=f"**{current_player.mention}**'s turn! Ask for some hints.\nWhen you're ready, use `/cycle answer <anime_id>` to submit your answer.",
          ),
          view=turn_view
        )

        await asyncio.sleep(1)
        timeout -= not is_last_player

        # answered correctedly, so update leaderboard 
        if cycle_object.just_answered == 1:
          await leaderboard.edit(embed=cycle_object.leaderboard())

        # Skip: last player -> answer needs to be correct | not last player -> answer doesn't need to be correct
        if (is_last_player and cycle_object.just_answered == 1) or (not is_last_player and cycle_object.just_answered):
            timeout = cycle_object.just_answered = 0

      turn_view.stop()

      # Early terminate by a member
      if is_terminate:
        await turn_msg.delete()
        await ctx.send(embed=Embed(
          description=f"**{terminator.mention} terminated the game...**",
          color=Color.red()
        ))
        cycle_object.clean_up()
        return 

      cycle_object.advance_player()
    
    await turn_msg.delete()
    cycle_object.clean_up()
  
  @cycle.command(description="Pick an anime for your assigned player")
  async def pick(self, ctx: ApplicationContext, anime_id: int):
    """
    This command should be used in "picking" phase
    Pick an anime for assigned player using MAL anime id.
    """
    member: Member = ctx.author
    cycle_object: CycleClass = players_games.get(member)

    if not cycle_object:
      await ctx.respond(f"You are not in any anime cycle game.", ephemeral=True)
      return
    
    if cycle_object.current_phase() != "picking":
      await ctx.respond(f"The game is not in the picking phase!", ephemeral=True)
      return

    result = await get_anime_by_id(anime_id)
    if not result:
      await ctx.respond(f"Invalid anime id was provided.", ephemeral=True)
      return
    
    title, url, mal_id, image_url = result.data.title, result.data.url, result.data.mal_id, result.data.images.jpg.image_url

    target: Member = cycle_object.targets[member] # get member object of assigned player

    # assigned that player a dotmapped compact anime info
    cycle_object.player_animes[target] = DotMap(dict(title=title, url=url, mal_id=mal_id))

    pick_embed = Embed(
      description=f"You picked **[{title}]({url})** for {target.mention}!",
      image=image_url,
      color=Color.nitro_pink()
    )
    await ctx.respond(embed=pick_embed, ephemeral=True)

    req: int = len(cycle_object.player_animes) - cycle_object.player_count
    if req > 0: 
      await ctx.send(embed=Embed(description=f"There are {req} players who still need to pick an anime.", color=Color.yellow()))
    
  @cycle.command(description="Submit your answer here!")
  async def answer(self, ctx: ApplicationContext, anime_id: int):
    """
    This command should be used in "turns" phase
    Member will use this command to submit their answer
    """
    member: Member = ctx.author
    cycle_object: CycleClass = players_games.get(member)

    if not cycle_object:
      await ctx.respond(f"You are not in any anime cycle game.", ephemeral=True)
      return

    if cycle_object.current_phase() != "turns":
      await ctx.respond(f"The game is not in the turns phase!", ephemeral=True)
      return

    if member != cycle_object.current_player():
      await ctx.respond(f"It's not your turn yet!", ephemeral=True)
      return

    result = await get_anime_by_id(anime_id)
    if not result:
      await ctx.respond(f"Invalid anime id was provided.", ephemeral=True)
      return

    title, url, mal_id, image_url = result.data.title, result.data.url, result.data.mal_id, result.data.images.jpg.image_url

    target: DotMap = cycle_object.player_animes[member] # retrieve player's assigned anime

    correct = target.mal_id == mal_id
    guessed = f"{member.mention} guessed [{title}]({url})\n"
    embed = Embed(image=image_url)

    if correct:
      cycle_object.just_answered = 1
      guessed += "**Correct!** 🤓"
      embed.color = Color.brand_green()
      cycle_object.add_done(member)
      cycle_object.turn_done[member] = cycle_object.round
    else:
      cycle_object.just_answered = 2
      guessed += "**Not quite right... Try again!** 🥹"
      embed.color = Color.brand_red()

    embed.description = guessed
    answer_msg = await ctx.respond(embed=embed)
    msg = await answer_msg.original_response()
    await msg.delete(delay=5)


def setup(bot):
  bot.add_cog(MiniGames(bot))
