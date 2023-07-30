from discord.ext import commands
import discord
import config
import wavelink
# from wavelink.ext import spotify
from wavelink.exceptions import InvalidLavalinkResponse
from cogs import EXTENSIONS

class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=intents, **kwargs)

    async def setup_hook(self):
        # sc = spotify.SpotifyClient(
        #     client_id=config.spotify['client_id'],
        #     client_secret=config.spotify['client_secret']
        # )
        node: wavelink.Node = wavelink.Node(uri='http://lavalink.devamop.in:80', password='DevamOP')
        node1: wavelink.Node = wavelink.Node(uri='http://141.95.90.1:88', password='youshallnotpass')
        await wavelink.NodePool.connect(client=self, nodes=[node1,node])
        
        await self.load_extension('jishaku')
        for cog in EXTENSIONS:
            try:
                await self.load_extension(cog)
            except Exception as exc:
                print(f'Could not load extension {cog} due to {exc.__class__.__name__}: {exc}')
            


    async def on_command_error(self, context, exception ):
        print(exception)
        if isinstance(exception, commands.CommandNotFound):
            return await context.send('Kuch bhi mat likh bhai')
        if isinstance(exception, InvalidLavalinkResponse):
            return await context.send('Kuch toh gadbad hai bhai, mene <@327390030689730561> ko bhej diya hai dekhne ke liye')
        else:
            return await super().on_command_error(context, exception)

    
    
    async def on_ready(self):
        print(f'Logged on as {self.user} (ID: {self.user.id})')


intents = discord.Intents.default()
intents.message_content = True
bot = Bot(intents=intents)
import uvloop
uvloop.install()
bot.run(config.token)