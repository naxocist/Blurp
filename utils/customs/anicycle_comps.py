import discord
from discord import Interaction, Member, Embed, Color
from discord.ui import View, Button

from typing import List
from dotmap import DotMap
import asyncio
import random

from .game_state import minigame_objects, players_games


class InviteView(View):

    def __init__(self, cycle_object, timeout):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.cycle_object = cycle_object
        self.is_terminated = False
        self.terminator = None

    @discord.ui.button(label="join", style=discord.ButtonStyle.green, emoji="🤓")
    async def join(self, button: Button, interaction: Interaction):
        member: Member = interaction.user
        if member in self.cycle_object.players:
            await interaction.response.send_message(
                "You are already in the game!", ephemeral=True
            )
            return

        self.cycle_object.add_player(member)
        await interaction.response.send_message(f"{member.mention} joined!")

    @discord.ui.button(
        label="force start", style=discord.ButtonStyle.blurple, emoji="💀"
    )
    async def start(self, button: Button, interaction: Interaction):
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="terminate", style=discord.ButtonStyle.red)
    async def terminate(self, button: Button, interaction: Interaction):
        await interaction.response.defer()
        self.is_terminated = True
        self.terminator = interaction.user
        self.stop()


class TurnView(View):

    def __init__(self, is_last_player: bool):
        super().__init__()
        self.is_last_player = is_last_player
        self.is_terminated = False
        self.terminator = None

        next_player_button = Button(
            label="next player",
            style=discord.ButtonStyle.green,
            disabled=is_last_player,
        )
        next_player_button.callback = self.next_player
        self.add_item(next_player_button)

    async def next_player(self, interaction: Interaction):
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="terminate", style=discord.ButtonStyle.red)
    async def terminate(self, button: Button, interaction: Interaction):
        await interaction.response.defer()
        self.is_terminated = True
        self.terminator = interaction.user
        self.stop()


class PickView(View):
    def __init__(self):
        super().__init__()
        self.is_terminated = False
        self.terminator = None

    @discord.ui.button(label="terminate", style=discord.ButtonStyle.red)
    async def terminate(self, button: Button, interaction: Interaction):
        await interaction.response.defer()
        self.is_terminated = True
        self.terminator = interaction.user
        self.stop()


class CycleClass:
    # time limit in seconds
    join_timeout = 20
    pick_timeout = 180
    delay_after_pick = 5
    turn_timeout = 60

    phases = ["lobby", "picking", "turns"]

    def __init__(self):
        minigame_objects.append(self)

        self.players: List[Member] = []
        self.targets: dict[Member, Member] = {}
        self.given_by: dict[Member, Member] = {}
        self.player_animes: dict[Member, DotMap] = {}
        self.player_count = 0

        self.players_pick_event: dict[Member, asyncio.Event] = {}

        self.turn_done: dict[Member, int] = {}
        self.just_answered = (
            0  # 0: not yet answered, 1: answered (wrong), 2: answered (right)
        )
        self.answered_event = asyncio.Event()

        self.active_player_index = 0
        self.phase_index = 0
        self.round = 1
        self.done_players: List[Member] = []

    def add_player(self, player: Member):
        self.player_count += 1
        self.players.append(player)
        players_games[player] = self

    # shuffle and find derangements of players, then assigned players to each other
    def random_targets(self):
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
            description += f"**#{rank}**: {player.mention} **Round {self.turn_done[player]}**\n[{anime.title}]({anime.url}) ❮❮ {giver.mention}\n"

        if not description:
            description = "No one's here..."
        return Embed(
            title=".⋅˚₊‧ 🜲Leaderboard ‧₊˚ ⋅",
            description=description,
            color=Color.gold(),
        )

    def clean_up(self):
        for player in self.players:
            if player in players_games:
                players_games.pop(player, None)

        if self in minigame_objects:
            minigame_objects.remove(self)
