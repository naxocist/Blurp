from typing import Final
import os
from dotenv import load_dotenv

from discord import Intents, Client, Message, app_commands
import discord

from responses import get_response


load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

intents = Intents.default()
intents.message_content = True

activity = discord.Activity(name='for commands', type=discord.ActivityType.watching)
client = Client(intents=intents, activity=activity)

tree = app_commands.CommandTree(client)


async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('(The message was empty because intents were not enabled properly)')
        return 
    
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]

    try:
        response: str = get_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)



@client.event
async def on_message(message: Message) -> None:
    if(message.author == client.user):
        return 
    
    username: str = str(message.author) 
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')

    await send_message(message, user_message)



@tree.command(
    name="commandname",
    description="My first application Command",
    guild=discord.Object(id=12417128931)
)
async def first_command(interaction):
    await interaction.response.send_message("Hello!")


@client.event
async def on_ready() -> None:
    # await tree.sync(guild=discord.Object(id=))
    print(f'{client.user} is now running!')


if __name__ == '__main__':
    client.run(token=TOKEN)
   
# jikan = Jikan()
# def json_dump(data):
#     return json.dumps(data, indent=4)


'''
https://discord.com/oauth2/authorize?client_id=1248292283883851919&permissions=139589962816&integration_type=0&scope=bot
'''