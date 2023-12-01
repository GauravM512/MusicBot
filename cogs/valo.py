from msgspec import Struct
import discord
from discord.ext import commands
import aiohttp
import asyncio

class Images(Struct):
    small: str
    large: str
    triangle_down: str
    triangle_up: str

class Card(Struct):
    small: str
    large: str
    wide: str
    id : str


class Valormmr(Struct):
    currenttier: int
    currenttierpatched: str
    images: Images
    ranking_in_tier: int
    mmr_change_to_last_game: int
    elo: int
    games_needed_for_rating: int
    old: bool


class HighestRank(Struct):
    old : bool
    tier: int
    patched_tier: str
    season: str


class Account(Struct):
    puuid: str
    region: str
    account_level: int
    name: str
    tag: str
    card: Card
    last_update: str
    last_update_raw: int
    
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

