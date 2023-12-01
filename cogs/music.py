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
        self.auto = {883632064283439115:False}

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready!")


    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload : wavelink.TrackEventPayload
    ):
        player: wavelink.Player=payload.player
        try:
            await self.bot.wait_for("wavelink_track_start", timeout=300)
        except asyncio.TimeoutError:
            await player.disconnect()

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, payload : wavelink.TrackEventPayload
    ):  
        channel = self.bot.get_channel(1037404775064551424)
        embed = discord.Embed(title="Now Playing", description=f"[{payload.track.title}]({payload.track.uri})", color=discord.Color.blurple())
        embed.set_image(url=payload.original.thumb)
        await channel.send(embed=embed)


    @commands.command(aliases=["p"])
    async def play(self, ctx: Context, *args):
        """Play a song from YouTube"""
        query = " ".join(args)
        auto = self.auto.get(ctx.guild.id,False)
        if ctx.author.voice is None:
            await ctx.reply("Bhai Voice chat join karega pehle", mention_author=False)
            return

        if not query:
            await ctx.reply("Song toh likh bhai", mention_author=False)
            return
        player:wavelink.Player
        player = ctx.guild.voice_client or await ctx.author.voice.channel.connect(cls=wavelink.Player)
        player.autoplay = True

        if player.channel.id != ctx.author.voice.channel.id:
            await ctx.send("Bhai tujhe dikh nai ra me kahi aur baja raha hu", mention_author=False)

        tracks = await wavelink.YouTubeTrack.search(query)
        if isinstance(tracks, (list)):
            if not player.is_playing():
                await player.play(tracks[0],populate=auto)
                embed = discord.Embed(title="Now Playing", description=f"[{tracks[0].title}]({tracks[0].uri})", color=discord.Color.blurple())
                embed.set_image(url=tracks[0].thumb)
                await ctx.reply(embed=embed, mention_author=False)
            else:
                await player.queue.put_wait(tracks[0])
                await ctx.reply(f"Queued {tracks[0].title}", mention_author=False)

        elif isinstance(tracks, wavelink.YouTubePlaylist):
            await player.queue.put_wait(tracks)
            if not player.is_playing():
                track = player.queue.get()
                await player.play(track,populate=auto)
                # embed = discord.Embed(title="Now Playing", description=f"[{track.title}]({track.uri})", color=discord.Color.blurple())
                # embed.set_image(url=track.thumb)
                # await ctx.reply(embed=embed, mention_author=False)
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
        if not player.is_playing():
            await ctx.reply("kya pause karu jab kuch nai baj raha", mention_author=False)
            return
        await player.pause()
        await ctx.reply("pause kardia bhai",mention_author=False)

    @commands.command(aliases=["r"])
    async def resume(self, ctx:Context):
        """Resume the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if player.is_playing():
            await ctx.reply("pehle se baj raha h bhai", mention_author=False)
            return
        if player is None:
            await ctx.reply("kya resume karu jab kuch nai baj raha", mention_author=False)
            return
        await player.resume()
        await ctx.reply("resume kardia bhai",mention_author=False)

    @commands.command(aliases=["s","dc"])
    async def stop(self, ctx:Context):
        """Stop the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if player.queue.is_empty != True:
            player.queue.clear()
        await player.disconnect()
        self.auto[ctx.guild.id] = not self.auto.get(ctx.guild.id,False)
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["sk","n","next"])
    async def skip(self, ctx:Context):
        """Skip the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if not player.is_playing():
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
        if player.queue.is_empty:
            await ctx.reply("kya queue dikhau jab kuch queue khali hain")
            return
        embed = discord.Embed(title="Queue", description="", color=0x00ff00)
        for i, track in enumerate(player.queue, start=1):
            embed.description += f"{i}) {track.title}\n"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    async def remove(self, ctx:Context, index:int):
        """Remove a song from queue"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if player.queue.is_empty:
            await ctx.reply("kya remove karu jab kuch queue khali hain")
            return
        if index > len(player.queue):
            await ctx.reply("index bada hain queue se bhai")
            return
        del player.queue[index-1]
        await ctx.reply("remove kardia bhai",mention_author=False)

    @commands.command(aliases=["np"])
    async def now_playing(self, ctx:Context):
        """Show the current song"""
        check = await check_author(ctx)
        if not check:
            return
        player: wavelink.Player = ctx.guild.voice_client
        if not player.is_playing():
            await ctx.reply("kya dikhau jab kuch nai baj raha")
            return
        embed = discord.Embed(title="Now Playing", description=player.current.title, color=0x00ff00)
        embed.set_image(url=player.current.thumbnail)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(aliases=["vol"])
    async def volume(self, ctx:Context, volume:int | None):
        """Change the volume"""
        check = await check_author(ctx)
        if not check:
            return
        if volume is None:
            await ctx.reply(f"Current volume {ctx.guild.voice_client.volume}",mention_author=False)
            return
        player: wavelink.Player = ctx.guild.voice_client
        if volume > 100 or volume < 0:
            await ctx.reply("volume 0 se 100 ke beech me hona chahiye bhai")
            return
        await player.set_volume(volume)
        await ctx.reply(f"{volume} kardia volume",mention_author=False)

    @commands.command(aliases=["auto"])
    async def autoplay(self, ctx:Context):
        """Toggle autoplay"""
        check = await check_author(ctx)
        if not check:
            return
        view = Autoplay.autoview()
        view.add_item(Autoplay.on())
        view.add_item(Autoplay.off())
        view.children[0].disabled = self.auto.get(ctx.guild.id,False)
        view.children[1].disabled = not self.auto.get(ctx.guild.id,False)
        view.value = self.auto.get(ctx.guild.id,False)
        view.message = ctx
        await ctx.reply(view=view,mention_author=False)
        await view.wait()
        self.auto[ctx.guild.id] = view.value
        return
        



class Autoplay:
    class autoview(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.value:bool = False

        async def stop(self) -> None:
            self.clear_items()
            return super().stop()


    class on(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.green, label="On", row=0)

        async def callback(self, interaction: discord.Interaction):
            self.view.value = True
            await self.view.stop()
            await interaction.response.edit_message(view=self.view,content="AutoPlay On")

    class off(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.red, label="Off", row=0)

        async def callback(self, interaction: discord.Interaction):
            self.view.value = False
            await self.view.stop()
            await interaction.response.edit_message(view=self.view,content="AutoPlay Off")


    
    




async def setup(bot):
    await bot.add_cog(Music(bot))