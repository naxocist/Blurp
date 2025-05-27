import discord
from discord.ext import commands
from utils.nekosbest import get_img, to_is_phrase, actions_to_others, expressions
from utils.jikanv4 import get_random_anime

from credentials import TEST_GUILD_ID


class Animes(commands.Cog):

  def __init__(self, bot): 
    self.bot = bot
  
  @commands.slash_command(guild_ids=[TEST_GUILD_ID], description="Show your expression")
  async def expression(self, ctx, action: str = discord.Option(str, "What expression do you want to show?", choices=expressions)):
    image = await get_img(action)
    is_phrase_action = to_is_phrase(action)
    embed = discord.Embed(
      color=discord.Color.random(),
      image=image.url
    )
    await ctx.respond(f"{ctx.author.mention} {is_phrase_action}!", embed=embed)

  @commands.slash_command(guild_ids=[TEST_GUILD_ID], description="Perform an action to another user") 
  async def action(self, ctx, member: discord.Member, action: str = discord.Option(str, "What action do you want to perform?", choices=actions_to_others)):
    image = await get_img(action)
    embed = discord.Embed(
      color=discord.Color.random(),
      image=image.url
    )

    if action == "dance": action += " with"
    await ctx.respond(f"{ctx.author.mention} wants to {action} {member.mention}!", embed=embed)

  @commands.slash_command(guild_ids=[TEST_GUILD_ID], description="Get a random anime illustration")
  async def art(self, ctx, choice: str = discord.Option(str, "Choose your type", choices=["husbando", "kitsune", "neko", "waifu"])):
    result = await get_img(choice)

    image = result.url
    artist = result.artist_name if result.artist_name else "Unknown"
    artist_href = result.artist_href if result.artist_href else "N/A"
    source_url = result.source_url if result.source_url else "N/A"

    embed = discord.Embed(
      title=f"Here is your {choice}!",
      description=f"Artist: **[{artist}]({artist_href})**\nVisit **[source]({source_url})!**",
      image=image,
      color=discord.Color.random()
    )
    await ctx.respond(embed=embed)

  @commands.slash_command(guild_ids=[TEST_GUILD_ID], description="Get a random anime")
  # @commands.cooldown(1, 5, commands.BucketType.user)  # Limit to 1 use every 5 seconds
  async def anime(self, ctx):
    await ctx.defer()
    random_anime = await get_random_anime() # return DotMap object
    data = random_anime.data

    title = data.title
    url = data.url
    image = data.images.jpg.image_url
    genres = " ".join([f"`{genre.name}`" for genre in data.genres] if data.genres else ["`N/A`"])
    season = data.season
    year = data.year
    episodes = data.episodes if data.episodes else "N/A"
    score = f"`{data.score}`/10" if data.score else "`N/A`"
    ranked = f"#{data.rank}" if data.rank else "N/A"


    embed = discord.Embed(
      title=title,
      url=url,
      image=image,
      color=discord.Color.random()
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
