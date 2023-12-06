import discord
from discord.ext import commands
import aiohttp
import asyncio

from pydantic import BaseModel, Field

class Images(BaseModel):
    small: str = Field(..., description="URL for the small image")
    large: str = Field(..., description="URL for the large image")
    triangle_down: str = Field(..., description="URL for the triangle-down image")
    triangle_up: str = Field(..., description="URL for the triangle-up image")

class Card(BaseModel):
    small: str = Field(..., description="URL for the small card image")
    large: str = Field(..., description="URL for the large card image")
    wide: str = Field(..., description="URL for the wide card image")
    id: str = Field(..., description="Unique identifier for the card")

class Valormmr(BaseModel):
    currenttier: int = Field(..., description="Current tier of the player")
    currenttierpatched: str = Field(..., description="Current tier with patched rank")
    images: Images = Field(..., description="Object containing image URLs for the player")
    ranking_in_tier: int = Field(..., description="Player's ranking within their current tier")
    mmr_change_to_last_game: int = Field(..., description="MMR change from the last game")
    elo: int = Field(..., description="Player's current Elo rating")
    games_needed_for_rating: int = Field(..., description="Number of games needed for rating to update")
    old: bool = Field(..., description="Indicates whether the data is for the old or new system")

class HighestRank(BaseModel):
    old: bool = Field(..., description="Indicates whether the data is for the old or new system")
    tier: int = Field(..., description="Highest tier achieved")
    patched_tier: str = Field(..., description="Highest tier with patched rank")
    season: str = Field(..., description="Season in which the highest rank was achieved")

class Account(BaseModel):
    puuid: str = Field(..., description="Unique identifier for the player's account")
    region: str = Field(..., description="Player's region")
    account_level: int = Field(..., description="Player's account level")
    name: str = Field(..., description="Player's in-game username")
    tag: str = Field(..., description="Player's in-game tag")
    card: Card = Field(..., description="Object containing card information for the player")
    last_update: str = Field(..., description="Date and time when the data was last updated")
    last_update_raw: int = Field(..., description="Unix timestamp representation of the last update")

    
async def fetch_account(name: str, tag: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}') as resp:
            data = await resp.json()
            data = data.get('data')
            images = data.get('card')
            data['card'] = Card(**images)
            return Account(**data)

async def fetch(name: str, tag: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.henrikdev.xyz/valorant/v2/mmr/ap/{name}/{tag}') as resp:
            data = await resp.json()
            data = data.get('data')
            high= data.get('highest_rank')
            data=data.get('current_data')
            images = data.get('images')
            data['images'] = Images(**images)
            return Valormmr(**data),HighestRank(**high)

color = { 'Iron 1': 0x8d8d8d ,
        'Iron 2': 0x8d8d8d ,
        'Iron 3': 0x8d8d8d ,
        'Silver 1': 0x646363 ,
        'Silver 2': 0x646363 ,
        'Silver 3': 0x646363 ,
        'Gold 1': 0xbea614 ,
        'Gold 2': 0xbea614 ,
        'Gold 3': 0xbea614 ,
        'Platinum 1': 0x2e5b97 ,
        'Platinum 2': 0x2e5b97 ,
        'Platinum 3': 0x2e5b97 ,
        'Diamond 1': 0x833a8b ,
        'Diamond 2': 0x833a8b ,
        'Diamond 3': 0x833a8b ,
        'Ascendant 1': 0x33803b ,
        'Ascendant 2': 0x33803b ,
        'Ascendant 3': 0x33803b ,
        'Immortal 1': 0xa01f1f ,
        'Immortal 2': 0xa01f1f ,
        'Immortal 3': 0xa01f1f ,
        'Radiant': 0xac7303 }

class Valorant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def valo(self, ctx: commands.Context):
        user = await self.bot.db.get_user(ctx.author.id)
        data,user = await asyncio.gather(fetch(user[1], user[2]),fetch_account(user[1], user[2]))
        data,high = data
        rank = data.currenttierpatched
        embed = discord.Embed(title="Valorant MMR", description=f"**{user.name}#{user.tag}**", color=color.get(rank,0xFFFFFF))
        embed.add_field(name="Level", value=f"{user.account_level}", inline=False)
        embed.add_field(name="Current Rank", value=f"{data.currenttierpatched}", inline=False)
        embed.add_field(name="Highest Rank", value=f"{high.patched_tier} in season {high.season}", inline=False)
        embed.add_field(name="Current Elo", value=f"{data.elo}", inline=False)
        embed.add_field(name="Current MMR", value=f"{data.ranking_in_tier}", inline=False)
        embed.add_field(name="Last match MMR", value=f"{data.mmr_change_to_last_game}", inline=False)
        embed.set_thumbnail(url=f"{data.images.large}")
        embed.set_author(name=ctx.author.name ,icon_url=f"{user.card.small}")
        embed.set_image(url=f"{user.card.wide}")
        await ctx.send(embed=embed)

   
    

async def setup(bot):
    await bot.add_cog(Valorant(bot))
