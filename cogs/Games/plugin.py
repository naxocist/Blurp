from __future__ import annotations
from core import Bot
from .. import Plugin

import discord
from discord.ext import commands

import asyncio
import random


class Games(Plugin):
    def __init__(self, bot: Bot):
        self.bot = bot
    

    @commands.command()
    async def g(self, ctx):
        bot = self.bot

        # if ctx.author.voice is None:
        #     await ctx.send(f"You must be in a voice channel! {ctx.author.mention} ")
        #     return
        
        players = [ctx.author]
        # voice_channel = ctx.author.voice.channel

        # await ctx.send(f"The game starts in {voice_channel.mention}")

        await ctx.send("If you want to join this game, type **join**")

        while True:
            try:
                response = await bot.wait_for('message', timeout=2,
                                              check=lambda m: m.author != bot.user and m.channel == ctx.channel and m.content == "join" \
                                                  and m.author not in players)
                                                    # and m.author.voice.channel == ctx.author.voice.channel)

                players.append(response.author)

                await ctx.send(f'{response.author.mention} joined!')

            except asyncio.TimeoutError:

                await ctx.send('Time\'s up!')

                random.shuffle(players)

                description = 'Here\'s the players...\n'
                for idx, player in enumerate(players, start=1):
                    description += f'#{idx}: {player.mention}\n'
                
                embed_info = discord.Embed(title='Players summary', description=description)
                await ctx.send(embed=embed_info)
                break

        ids = { p: idx for idx, p in enumerate(players) }
        
        pairs = [(i+1)%len(players) for i in range(len(players))]

        tasks = []
        for idx, p in enumerate(players):
            nxt = players[pairs[idx]]

            embed_pick = discord.Embed(title=f"Pick an anime for {nxt.name} to guess!", colour=discord.Colour.random())
            embed_pick.description = "please send me the chosen anime's MAL id here"
            embed_pick.set_image(url=nxt.avatar.url)
            embed_pick.set_footer(icon_url=bot.user.avatar.url, text="This person will be guessing the chosen anime...")

            await p.send(embed=embed_pick)

            task = asyncio.create_task(bot.wait_for('message', check=lambda m: m.author == p and isinstance(m.channel, discord.DMChannel), timeout=5))
            tasks.append(task)
        
        done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

        assigned_animes = {}
        for task in done:
            if task.exception():
                # This player didn't send anime id, therefore random an anime
                continue

            message = task.result()
            MAL_id = message.content
            # validate MAL id

            author_id = ids[message.author]
            assigned_animes[pairs[author_id]] = MAL_id

        turn = 0
        while True:
            await ctx.send(players[turn].mention + ", it's your turn!")

            turn += 1
            turn %= len(players)
    

async def setup(bot: Bot):
    await bot.add_cog(Games(bot))