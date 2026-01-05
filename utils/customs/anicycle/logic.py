import asyncio
from typing import cast

from discord import ApplicationContext, Color, Embed, Member
from nekosbest import Result

from utils.apis.nekosbest import get_img
from utils.customs.anicycle.comps import (CycleClass, InviteView, PickView,
                                          TurnView)
from utils.customs.tools import \
    count_down_timer  # discord embed countdown timer


async def init_phase(ctx: ApplicationContext):
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

    # too few players
    if cycle_obj.player_count < 2:
        await ctx.send(
            embed=Embed(
                title="Anime Cycle terminated",
                description="You need at least 2 players!",
                color=Color.red(),
            ),
        )
        cycle_obj.clean_up()
        return None

    if invite_view.terminator is None:
        await ctx.respond("[Error] No terminator... weird.")
        return

    if invite_view.is_terminated:
        await ctx.send(
            embed=Embed(
                description=f"**{invite_view.terminator.mention} terminated the game...**",
                color=Color.red(),
            )
        )
        return None

    return cycle_obj


async def random_phase(ctx: ApplicationContext, cycle_obj):
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
            thumbnail=cast(Result, await get_img("thumbsup")).url,
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

    return pick_msg, pick_view


async def pick_phase(ctx: ApplicationContext, cycle_obj, pick_msg, pick_view):
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
        await asyncio.gather(*(wait_for_player(player) for player in cycle_obj.players))

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


async def game_phase(ctx: ApplicationContext, cycle_obj):
    # DM everyone about assigned anime info
    for player in cycle_obj.players:
        info = ""
        for plyr in cycle_obj.players:
            if plyr == player:
                continue
            assigned_anime = cycle_obj.player_animes[plyr]
            info += (
                f"{plyr.mention} ❮❮ [{assigned_anime.title}]({assigned_anime.url})\n"
            )

        if player.bot:
            continue
        await player.send(
            embed=Embed(title="Information", description=info, colour=Color.blurple())
        )

    # after pick delay, let players look at the sent info
    await count_down_timer(
        ctx, cycle_obj.delay_before_turn, title_prefix="Game start in:"
    )

    # Initial turn setup
    turn_msg = await ctx.send(
        embed=Embed(
            title=f"Round {cycle_obj.round} | ⏱︎ Time left: {
                cycle_obj.turn_timeout
            } secs | Player left: {cycle_obj.player_count}",
            description=f"{
                cycle_obj.current_player().mention
            }'s turn! Ask for some hints.\nWhen you're ready, use `/cycle answer <anime_id>` to submit your answer.",
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
                        title=f"Round {cycle_obj.round} | ⏱︎ Time left: {
                            str(timeout) + ' secs' if not is_last_player else '-'
                        } | Players left: {player_left}",
                        description=f"{
                            current_player.mention
                        }'s turn! Ask for some hints.\nWhen you're ready, use `/cycle answer <anime_id>` to submit your answer.",
                    ),
                    view=turn_view,
                )
            sleep_task = asyncio.create_task(asyncio.sleep(1))
            answered_task = asyncio.create_task(cycle_obj.answered_event.wait())
            view_task = asyncio.create_task(turn_view.wait())

            done, _ = await asyncio.wait(
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

        if turn_view.terminator is None:
            await ctx.respond("[ERROR] No terminator... weird.")
            return
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
