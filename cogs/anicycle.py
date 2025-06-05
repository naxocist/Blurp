from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Bot
from dotmap import DotMap
import discord

import asyncio

# apis
from utils.apis.jikanv4 import get_anime_by_id
from utils.apis.nekosbest import get_img

# customs - UI & state
from utils.customs.anicycle_comps import InviteView, TurnView, PickView, CycleClass
from utils.customs.commands import count_down_timer
from utils.customs.game_state import players_games

from credentials import guild_ids


class AniCycle(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    cycle = discord.SlashCommandGroup(
        "cycle", "anime cycle game commands", guild_ids=guild_ids
    )

    @cycle.command(description="Initialize an anime cycle game")
    async def init(self, ctx: ApplicationContext):
        await ctx.defer()

        cycle_obj = CycleClass()

        invite_view = InviteView(cycle_obj, cycle_obj.join_timeout)
        intro_msg = await ctx.respond(
            embed=Embed(
                title="Anime Cycle has been initialized!", color=Color.nitro_pink()
            ),
            view=invite_view,
        )

        await invite_view.wait()
        invite_view.disable_all_items()
        await intro_msg.edit(view=invite_view)

        if invite_view.is_terminated:
            await ctx.send(
                embed=Embed(
                    description=f"**{invite_view.terminator.mention} terminated the game...**",
                    color=Color.red(),
                )
            )
            return

        # DEMO data
        # cycle_obj.add_player(ctx.author)
        # cycle_obj.add_player(self.bot.user)
        # cycle_obj.player_animes[ctx.author] = DotMap(
        #     dict(
        #         title="Aharen-san wa Hakarenai Season 2",
        #         url="https://myanimelist.net/anime/59466/Aharen-san_wa_Hakarenai_Season_2",
        #         mal_id=59466,
        #     )
        # )

        # too few players to start the game
        if cycle_obj.player_count < 2:
            await ctx.send(
                embed=Embed(
                    title="Anime Cycle terminated",
                    description="You need at least 2 players!",
                    color=Color.red(),
                ),
            )
            cycle_obj.clean_up()
            return

        # assign every player another player
        cycle_obj.random_targets()

        # * LOBBY & PAIRING STATUS
        players_list = ", ".join([player.mention for player in cycle_obj.players])
        pairs_info = ""
        for player in cycle_obj.players:
            target = cycle_obj.targets[player]
            pairs_info += f"{player.mention} ➜ {target.mention}\n"

        await ctx.send(
            embed=Embed(
                title="Lobby",
                description=players_list,
                thumbnail=(await get_img("thumbsup")).url,
                color=Color.brand_green(),
            ).add_field(name="Pairing", value=pairs_info)
        )

        # * PICKING: each players pick an anime for their target using /pick command
        cycle_obj.advance_phase()

        pick_view = PickView()

        pick_msg = await ctx.send(
            embed=Embed(
                title="use `/cycle pick <anime_id>` to pick an anime for your pair",
                description="You must find an anime id on [MyAnimeList](https://myanimelist.net/) only\nExample: https://myanimelist.net/anime/9776/A-Channel\n`9776` is the anime id\n"
                + cycle_obj.get_pick_status(),
                color=Color.yellow(),
            ),
            view=pick_view,
        )

        # assigned pick asyncio.Event to every player (listen for /cycle pick)
        for player in cycle_obj.players:
            cycle_obj.players_pick_event[player] = asyncio.Event()

        async def wait_for_player(player: Member):
            if player.bot:
                return
            await cycle_obj.players_pick_event[player].wait()
            # edit picking interface
            await pick_msg.edit(
                embed=Embed(
                    title="use `/cycle pick <anime_id>` to pick an anime for your pair",
                    description="You must find an anime id on [MyAnimeList](https://myanimelist.net/) only\nExample: https://myanimelist.net/anime/9776/A-Channel\n`9776` is the anime id\n"
                    + cycle_obj.get_pick_status(),
                    color=Color.yellow(),
                ),
            )

        async def wait_for_all_players():
            await asyncio.gather(
                *(wait_for_player(player) for player in cycle_obj.players)
            )

        player_group_task = asyncio.create_task(wait_for_all_players())
        terminate_task = asyncio.create_task(pick_view.wait())

        done, pending = await asyncio.wait(
            [player_group_task, terminate_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # clean up pending tasks
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

        if terminate_task in done:
            # Termination happened first: cancel all player tasks
            player_group_task.cancel()

            pick_view.disable_all_items()
            await pick_msg.edit(view=pick_view)
            await ctx.send(
                embed=Embed(
                    description=f"**{pick_view.terminator.mention} terminated the game...**",
                    color=Color.red(),
                )
            )
            cycle_obj.clean_up()
            return
        else:
            terminate_task.cancel()

        pick_view.disable_all_items()
        await pick_msg.edit(view=pick_view)
        await pick_msg.delete()

        # DM everyone about assigned anime info
        for player in cycle_obj.players:
            info = ""
            for plyr in cycle_obj.players:
                if plyr == player:
                    continue
                assigned_anime = cycle_obj.player_animes[plyr]
                info += f"{plyr.mention} ❮❮ [{assigned_anime.title}]({assigned_anime.url})\n"

            if player.bot:
                continue
            await player.send(
                embed=Embed(
                    title="Information", description=info, colour=Color.blurple()
                )
            )

        # after pick delay, let players look at the sent info
        await count_down_timer(
            ctx, cycle_obj.delay_before_turn, title_prefix="Game start in:"
        )

        # Initial turn setup
        turn_msg = await ctx.send(
            embed=Embed(
                title=f"Round {cycle_obj.round} | ⏱︎ Time left: {cycle_obj.turn_timeout} secs | Player left: {cycle_obj.player_count}",
                description=f"{cycle_obj.current_player().mention}'s turn! Ask for some hints.\nWhen you're ready, use `/cycle answer <anime_id>` to submit your answer.",
                color=Color.purple(),
            ),
            view=TurnView(is_last_player=False),
        )

        leaderboard = await ctx.send(embed=cycle_obj.leaderboard())

        # * Turn: Now the game starts, each player will take turns to get hints or take a guess about their assigned anime
        cycle_obj.advance_phase()
        while len(cycle_obj.done_players) < cycle_obj.player_count:
            player_left = cycle_obj.player_count - len(cycle_obj.done_players)
            current_player = cycle_obj.current_player()

            if current_player in cycle_obj.done_players:
                cycle_obj.advance_player()
                continue

            is_last_player = player_left == 1
            turn_view = TurnView(is_last_player=is_last_player)

            timeout = cycle_obj.turn_timeout

            while timeout > 0:
                if timeout and (timeout % 5 == 0 or timeout <= 10):
                    await turn_msg.edit(
                        embed=Embed(
                            title=f"Round {cycle_obj.round} | ⏱︎ Time left: {str(timeout) + " secs" if not is_last_player else "-"} | Players left: {player_left}",
                            description=f"{current_player.mention}'s turn! Ask for some hints.\nWhen you're ready, use `/cycle answer <anime_id>` to submit your answer.",
                        ),
                        view=turn_view,
                    )
                sleep_task = asyncio.create_task(asyncio.sleep(1))
                answered_task = asyncio.create_task(cycle_obj.answered_event.wait())
                view_task = asyncio.create_task(turn_view.wait())

                done, pending = await asyncio.wait(
                    [sleep_task, answered_task, view_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # triggered a button
                if view_task in done:
                    break

                if answered_task in done:
                    cycle_obj.answered_event.clear()
                    # answered correctedly, so update leaderboard
                    if cycle_obj.just_answered == 1:
                        await leaderboard.edit(embed=cycle_obj.leaderboard())

                    # skip turn if answer
                    break
                elif not is_last_player:
                    timeout -= 1

            # Early terminate by a member
            if turn_view.is_terminated:
                await turn_msg.delete()
                await ctx.send(
                    embed=Embed(
                        description=f"**{turn_view.terminator.mention} terminated the game...**",
                        color=Color.red(),
                    )
                )
                cycle_obj.clean_up()
                return

            cycle_obj.advance_player()

        await turn_msg.delete()
        cycle_obj.clean_up()

    @cycle.command(description="Pick an anime for your assigned player")
    async def pick(self, ctx: ApplicationContext, anime_id: int):
        """
        This command should be used in "picking" phase
        Pick an anime for assigned player using MAL anime id.
        """
        member: Member = ctx.author
        cycle_obj: CycleClass = players_games.get(member)

        if not cycle_obj:
            await ctx.respond(f"You are not in any anime cycle game.", ephemeral=True)
            return

        if cycle_obj.current_phase() != "picking":
            await ctx.respond(f"The game is not in the picking phase!", ephemeral=True)
            return

        result = await get_anime_by_id(anime_id)
        if not result:
            await ctx.respond(f"Invalid anime id was provided.", ephemeral=True)
            return

        title, url, mal_id, image_url = (
            result.data.title,
            result.data.url,
            result.data.mal_id,
            result.data.images.jpg.image_url,
        )

        target: Member = cycle_obj.targets[
            member
        ]  # get member object of assigned player

        # assigned that player a dotmapped compact anime info
        cycle_obj.player_animes[target] = DotMap(
            dict(title=title, url=url, mal_id=mal_id)
        )

        pick_embed = Embed(
            description=f"You picked **[{title}]({url})** for {target.mention}!",
            image=image_url,
            color=Color.nitro_pink(),
        )
        await ctx.respond(embed=pick_embed, ephemeral=True)

        # trigger pick event
        cycle_obj.add_picked(member)

    @cycle.command(description="Submit your answer here!")
    async def answer(self, ctx: ApplicationContext, anime_id: int):
        """
        This command should be used in "turns" phase
        Member will use this command to submit their answer
        """
        member: Member = ctx.author
        cycle_obj: CycleClass = players_games.get(member)

        if not cycle_obj:
            await ctx.respond(f"You are not in any anime cycle game.", ephemeral=True)
            return

        if not isinstance(cycle_obj, CycleClass):
            await ctx.respond(f"You are not in anicycle minigame...", ephemeral=True)
            return

        if cycle_obj.current_phase() != "turns":
            await ctx.respond(f"The game is not in the turns phase!", ephemeral=True)
            return

        if member != cycle_obj.current_player():
            await ctx.respond(f"It's not your turn yet!", ephemeral=True)
            return

        result = await get_anime_by_id(anime_id)
        if not result:
            await ctx.respond(f"Invalid anime id was provided.", ephemeral=True)
            return

        title, url, mal_id, image_url = (
            result.data.title,
            result.data.url,
            result.data.mal_id,
            result.data.images.jpg.image_url,
        )

        target: DotMap = cycle_obj.player_animes[
            member
        ]  # retrieve player's assigned anime

        correct = target.mal_id == mal_id
        guessed = f"{member.mention} guessed [{title}]({url})\n"
        embed = Embed(image=image_url)

        if correct:
            cycle_obj.just_answered = 1
            guessed += "**Correct!** 🤓"
            embed.color = Color.brand_green()
            cycle_obj.add_done(member)
            cycle_obj.turn_done[member] = cycle_obj.round
        else:
            cycle_obj.just_answered = 2
            guessed += "**Not quite right... Try again!** 🥹"
            embed.color = Color.brand_red()

        embed.description = guessed
        answer_msg = await ctx.respond(embed=embed)
        cycle_obj.answered_event.set()  # trigger answered flag

        msg = await answer_msg.original_response()
        await msg.delete(delay=5)


def setup(bot):
    bot.add_cog(AniCycle(bot))
