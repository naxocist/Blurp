import discord
from discord.ext import commands
from discord import Member, ApplicationContext, Embed, Color, Bot, Option

from utils.apis.nekosbest import get_img, to_is_phrase, actions_to_others, expressions
from utils.apis.jikanv4 import get_random_anime

from credentials import guild_ids

class Animes(commands.Cog):

  def __init__(self, bot): 
    self.bot: Bot = bot
  
  # expression emotions through gifs
  @commands.slash_command(guild_ids=guild_ids, description="Express your emotions")
  async def expression(self, ctx: ApplicationContext, action: Option = Option(str, "What expression do you want to show?", choices=expressions)):
    await ctx.defer()

    image = await get_img(action)
    is_phrase_action = to_is_phrase(action)
    embed = Embed(
      image=image.url, 
      color=Color.random()
    )
    await ctx.respond(f"{ctx.author.mention} {is_phrase_action}!", embed=embed)

  # actions to other members through gifs
  @commands.slash_command(guild_ids=guild_ids, description="Perform an action to another user") 
  async def action(self, ctx: ApplicationContext, member: Member, action: Option = Option(str, "What action do you want to perform?", choices=actions_to_others)):
    await ctx.defer()

    image = await get_img(action)
    embed = Embed(
      image=image.url,
      color=Color.random()
    )

    if action == "dance": action += " with"
    await ctx.respond(f"{ctx.author.mention} wants to {action} {member.mention}!", embed=embed)

  # get a random anime illustration
  @commands.slash_command(guild_ids=guild_ids, description="Get a random anime illustration")
  async def art(self, ctx: ApplicationContext, choice: str = discord.Option(str, "Choose your type", choices=["husbando", "kitsune", "neko", "waifu"])):
    await ctx.defer()

    result = await get_img(choice)
    image = result.url
    artist = result.artist_name or "Unknown"
    artist_href = result.artist_href or "N/A"
    source_url = result.source_url or "N/A"

    embed = Embed(
      title=f"Here is your {choice}!",
      description=f"Artist: **[{artist}]({artist_href})**\nVisit **[source]({source_url})!**",
      image=image,
      color=Color.random()
    )

    await ctx.respond(embed=embed)

  # get a random anime based on jikan-v4 API
  @commands.slash_command(guild_ids=guild_ids, description="Get a random anime")
  async def anime(self, ctx):
    await ctx.defer()

    random_anime = await get_random_anime() # recieve DotMap object
    data = random_anime.data

    title = data.title
    url = data.url
    image = data.images.jpg.image_url
    genres = " ".join([f"`{genre.name}`" for genre in data.genres] if data.genres else ["`N/A`"])
    season = data.season
    year = data.year
    episodes = data.episodes or "N/A"
    score = f"`{data.score}`/10" or "`N/A`"
    ranked = f"#{data.rank}" or "N/A"


    embed = Embed(
      title=title,
      url=url,
      image=image,
      color=Color.random()
    )

    embed.add_field(name="Genres", value=genres, inline=False)
    embed.add_field(name="Season", value=f"`{season.capitalize() + " " + str(year) if season and year else "N/A"}`", inline=True)
    embed.add_field(name="Length", value=f"`{episodes}` episodes", inline=True)
    embed.add_field(name="Score", value=f"{score}", inline=True)
    embed.add_field(name=f"Ranked: `{ranked}`", value="", inline=False)
    
    response = await ctx.respond(embed=embed)
    await discord.Message.add_reaction(response, "📬") 


def setup(bot):
  bot.add_cog(Animes(bot))
