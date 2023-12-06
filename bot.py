from discord.ext import commands
import discord
import config
import wavelink
import asqlite
from cogs import EXTENSIONS


class Database:
    def __init__(self,db):
        self.db: asqlite.Connection = db
    table = """CREATE TABLE IF NOT EXISTS valo (
        id INTEGER PRIMARY KEY,
        name TEXT,
        tag TEXT
    )"""
    add = """INSERT OR REPLACE INTO valo (id, name, tag) VALUES (?, ?, ?);"""
    delete = """DELETE FROM valo WHERE id = ?"""
    get = """SELECT * FROM valo WHERE id = ?"""
    async def create_table(self):
        async with self.db.cursor() as cursor:
            await cursor.execute(self.table)
            await self.db.commit()
    
    async def add_user(self, id,name, tag):
        async with self.db.cursor() as cursor:
            await cursor.execute(self.add, (id,name, tag))
            await self.db.commit()

    async def delete_user(self, id):
        async with self.db.cursor() as cursor:
            await cursor.execute(self.delete, (id,))
            await self.db.commit()
        
    async def get_user(self, id):
        async with self.db.cursor() as cursor:
            await cursor.execute(self.get, (id,))
            return await cursor.fetchone()
    
    async def close(self):
        await self.db.close()

class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=intents, **kwargs)

    async def setup_hook(self):
        self.db = Database(await asqlite.connect('database.db'))
        await self.db.create_table()
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')
        await wavelink.Pool.connect(client=self,nodes=[node])
        
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
        else:
            return await super().on_command_error(context, exception)

    async def close(self) -> None:
        await self.db.close()
        return await super().close()
    
    
    async def on_ready(self):
        print(f'Logged on as {self.user} (ID: {self.user.id})')


intents = discord.Intents.default()
intents.message_content = True
bot = Bot(intents=intents)
import uvloop
uvloop.install()
bot.run(config.token)