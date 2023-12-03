import asyncio
import discord
import wavelink
from discord.ext import commands
from discord.ext.commands import Context


async def check_author(ctx: Context):
    if ctx.author.voice is None:
        await ctx.reply("Bhai Voice chat join karega pehle", mention_author=False)
        return False
    return True

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"Node {payload.node!r} is ready!")


    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload : wavelink.TrackEndEventPayload
    ):
        player: wavelink.Player=payload.player
        try:
            await self.bot.wait_for("wavelink_track_start", timeout=300)
        except asyncio.TimeoutError:
            await player.disconnect()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self,payload: wavelink.TrackStartEventPayload):
        channel=payload.original.channel
        embed = discord.Embed(title="Now Playing", description=f"[{payload.track.title}]({payload.track.uri})", color=discord.Color.blurple())
        embed.add_field(name="Requested by", value=f"{payload.original.requester}", inline=False)
        embed.set_image(url=payload.track.artwork)
        await channel.send(embed=embed)


    @commands.command(aliases=["p"])
    async def play(self, ctx: Context, *args):
        """Play a song from YouTube"""
        query = " ".join(args)
        if ctx.author.voice is None:
            await ctx.reply("Bhai Voice chat join karega pehle", mention_author=False)
            return

        if not query:
            await ctx.reply("Song toh likh bhai", mention_author=False)
            return
        player:wavelink.Player
        player = ctx.guild.voice_client or await ctx.author.voice.channel.connect(cls=wavelink.Player)

        if player.channel.id != ctx.author.voice.channel.id:
            await ctx.send("Bhai tujhe dikh nai ra me kahi aur baja raha hu", mention_author=False)

        tracks = await wavelink.Playable.search(query)
        if isinstance(tracks, (list)):
            if not player.playing:
                tracks[0].channel=ctx.channel
                tracks[0].requester=ctx.author.display_name
                await player.play(tracks[0])
                player.autoplay= wavelink.AutoPlayMode.partial
            else:
                tracks[0].channel=ctx.channel
                tracks[0].requester=ctx.author.display_name
                await player.queue.put_wait(tracks[0])
                await ctx.reply(f"Queued {tracks[0].title}", mention_author=False)

        elif isinstance(tracks, wavelink.Playlist):
            for track in tracks:
                track.channel=ctx.channel
                track.requester=ctx.author.display_name
            await player.queue.put_wait(tracks)
            if not player.playing:
                track = player.queue.get()
                await player.play(track)
            else:
                await ctx.reply(f"Queued Playlist ", mention_author=False)

        else:
            reply_message = "Kuch nai mila bhai"
            await ctx.reply(reply_message, mention_author=False)


    @commands.command(aliases=["pa"])
    async def pause(self, ctx:Context):
        """Pause the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if not player.playing:
            await ctx.reply("kya pause karu jab kuch nai baj raha", mention_author=False)
            return
        await player.pause(True)
        await ctx.reply("pause kardia bhai",mention_author=False)

    @commands.command(aliases=["r"])
    async def resume(self, ctx:Context):
        """Resume the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if player is None:
            await ctx.reply("kya resume karu jab kuch nai baj raha", mention_author=False)
            return
        await player.pause(False)
        await ctx.reply("resume kardia bhai",mention_author=False)

    @commands.command(aliases=["s","dc"])
    async def stop(self, ctx:Context):
        """Stop the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        player.queue.clear()
        await player.disconnect()
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["sk","n","next"])
    async def skip(self, ctx:Context):
        """Skip the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if not player.playing:
            await ctx.reply("kya skip karu jab kuch nai baj raha",mention_author=False)
            return
        await player.stop()
        await ctx.reply("skip kardia bhai",mention_author=False)

    @commands.command(aliases=["q"])
    async def queue(self, ctx:Context):
        """Show the current queue"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if player.queue==None:
            await ctx.reply("kya queue dikhau jab kuch queue khali hain")
            return
        embed = discord.Embed(title="Queue", description="", color=0x00ff00)
        for i, track in enumerate(player.queue, start=1):
            embed.description += f"{i}) {track.title} requester: {track.requester}\n"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    async def remove(self, ctx:Context, index:int):
        """Remove a song from queue"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if index > len(player.queue):
            await ctx.reply("index bada hain queue se bhai")
            return
        await player.queue.delete(index-1)
        await ctx.reply("remove kardia bhai",mention_author=False)

    @commands.command(aliases=["np"])
    async def now_playing(self, ctx:Context):
        """Show the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if not player.playing:
            await ctx.reply("kya dikhau jab kuch nai baj raha")
            return
        embed = discord.Embed(title="Now Playing", description=player.current.title, color=0x00ff00)
        embed.set_image(url=player.current.artwork)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(aliases=["vol"])
    async def volume(self, ctx:Context, volume:int | None):
        """Change the volume"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if volume is None:
            await ctx.reply(f"Current volume {player.volume}",mention_author=False)
            return
        if volume > 100 or volume < 0:
            await ctx.reply("volume 0 se 100 ke beech me hona chahiye bhai")
            return
        await player.set_volume(volume)
        await ctx.reply(f"{volume} kardia volume",mention_author=False)

 
    @commands.command(aliases=["ping"])
    async def latency(self, ctx:Context):
        """Show the bot's latency and lavalink latency"""
        player : wavelink.Player = ctx.guild.voice_client
        await ctx.reply(f"Bot latency: {round(self.bot.latency * 1000)}ms\nLavalink latency: {round(player.ping)}ms",mention_author=False)




async def setup(bot):
    await bot.add_cog(Music(bot))