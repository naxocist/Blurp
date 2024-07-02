import discord
from discord.ext import commands

import settings

import asyncio

from responses import get_response

import random


intents = discord.Intents.default()
intents.message_content = True

logger = settings.logging.getLogger("bot")

activity = discord.Activity(name='for commands', type=discord.ActivityType.watching)
bot = commands.Bot(command_prefix='.', intents=intents, activity=activity)


@bot.command()
async def t(ctx) -> None:

    def check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    message = await bot.wait_for('message', check=check, timeout=10)

    embed = discord.Embed()

    embed.title = 'This is title'
    embed.description = 'This is description'
    embed.colour = discord.Colour.blue()

    file = discord.File('./assets/profile.jpeg', filename="profile.jpeg")
    embed.set_image(url='attachment://profile.jpeg')
    embed.set_thumbnail(url='attachment://profile.jpeg')
    embed.set_footer(text='This is foother', icon_url=ctx.author.avatar.url)
    embed.set_author(name=ctx.author.nick, url='https://www.google.co.th/', icon_url=ctx.author.avatar.url)

    embed.add_field(name='this is name', value='this is value', inline=True)
    embed.add_field(name='this is name', value='this is value', inline=True)

    await ctx.send(file=file, embed=embed)


@bot.command()
async def g(ctx) -> None:

    # if ctx.author.voice is None:
    #     await ctx.send(f"You must be in a voice channel! {ctx.author.mention} ")
    #     return
    
    players = [ctx.author]
    # voice_channel = ctx.author.voice.channel

    # await ctx.send(f"The game starts in {voice_channel.mention}")
    

    def check(m):
        return m.author != bot.user and m.channel == ctx.channel and m.content == "join" and m.author not in players

    await ctx.send(embed=discord.Embed(title='If you want to join this game, type \"join\"'))

    while True:
        try:
            response = await bot.wait_for('message', check=check, timeout=5)

            players.append(response.author)

            await ctx.send(f'{response.author.mention} joined!')

        except asyncio.TimeoutError:

            await ctx.send('Time\'s up!')

            random.shuffle(players)

            description = 'Here\'s the players order..\n'
            for idx, player in enumerate(players, start=1):
                description += f'#{idx}: {player.mention}\n'
            
            embed_info = discord.Embed(title='Players summary', description=description)
            await ctx.send(embed=embed_info)
            break

    ids = { p: idx for idx, p in enumerate(players) }

    print(ids)
    
    players_number = len(players)
    pairs = [(i+1)%players_number for i in range(players_number)]

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
            # This player didn't send anime id
            continue

        message = task.result()
        MAL_id = message.content
        author_id = ids[message.author]

        assigned_animes[pairs[author_id]] = MAL_id
    
@bot.command()
async def pt(ctx, tag) -> None:
    # if not isinstance(tag, discord.Member.mention):
    #     await ctx.send("Please tag someone!")
    
    print(type(tag))
    await ctx.send(tag)


@bot.event
async def on_ready():
    logger.info(f"User: {bot.user} (ID: {bot.user.id})")


bot.run(settings.TOKEN, root_logger=True)

'''
https://discord.com/oauth2/authorize?client_id=1248292283883851919&permissions=139589962816&integration_type=0&scope=bot
'''