import asyncio
import re

import discord
import wavelink
from discord.ext import commands
from discord.ext.commands import Context


async def link_validation(link: str):
    playlist_regex = r"^(https?:\/\/)?(www\.)?(youtube\.com)\/(playlist\?|watch\?)(list=)([a-zA-Z0-9_-]+)"
    video_regex = r"^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/(watch\?v=|embed\/|v\/)?([a-zA-Z0-9_-]+)"

    if re.match(playlist_regex, link):
        # Check if the link contains the "list" parameter
        if "list=" in link:
            return "playlist"

    elif re.match(video_regex, link):
        return "video"

    else:
        return "string"


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready!")


    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload : wavelink.TrackEventPayload
    ):
        player: wavelink.Player=payload.player
        if not player.queue.is_empty:
            track = player.queue.get()
            await player.play(track)
        try:
            await self.bot.wait_for("wavelink_track_start", timeout=300)
        except asyncio.TimeoutError:
            await player.disconnect()


    @commands.command(aliases=["p"])
    async def play(self, ctx: Context, *args):
        """Play a song from YouTube"""
        query = " ".join(args)
        media_type = await link_validation(query)

        if ctx.author.voice is None:
            await ctx.reply("Bhai Voice chat join karega pehle", mention_author=False)
            return

        if not query:
            await ctx.reply("Song toh likh bhai", mention_author=False)
            return

        if not ctx.guild.voice_client:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            player = ctx.guild.voice_client
        
        if player.channel.id != ctx.author.voice.channel.id:
            if player.is_playing():
                await ctx.send("Bhai tujhe dikh nai ra me kahi aur baja raha hu", mention_author=False)
                return
            else:
                await player.disconnect()
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        if ctx.guild.voice_client:
            player = ctx.guild.voice_client
            if player.is_playing():
                if media_type == "playlist":
                    return await ctx.reply("Playlist nai bajata me.", mention_author=False)
                if media_type == "video":
                    query = re.sub(r"list=[^&?]+", "", query)
                track = await wavelink.YouTubeTrack.search(query)
                player.queue.put(track[0])
                embed = discord.Embed(title="Added to Queue", description=track[0].title, color=0x00ff00)
                embed.set_image(url=track[0].thumbnail)
                await ctx.reply(embed=embed, mention_author=False)
                return

        if media_type == "playlist":
            await ctx.reply("Sorry bhai playlist nai bajata me", mention_author=False)
            return

        if media_type in ["string", "video"]:
            query = re.sub(r"list=[^&?]+", "", query)
            tracks = await wavelink.YouTubeTrack.search(query)
            await player.play(tracks[0])
            embed = discord.Embed(title="Now Playing", description=tracks[0].title, color=0x00ff00)
            embed.set_image(url=tracks[0].thumbnail)
            await ctx.reply(embed=embed)
            return

        if not tracks:
            await ctx.reply("Dhang se likh na lawde kuch result nai aya", mention_author=False)
            return

        


    @commands.command(aliases=["pa"])
    async def pause(self, ctx:Context):
        """Pause the current song"""
        player: wavelink.Player = ctx.guild.voice_client
        if not player.is_playing():
            await ctx.reply("kya pause karu jab kuch nai baj raha", mention_author=False)
            return
        await player.pause()
        await ctx.reply("pause kardia bhai",mention_author=False)

    @commands.command(aliases=["r"])
    async def resume(self, ctx:Context):
        """Resume the current song"""
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
        player: wavelink.Player = ctx.guild.voice_client
        if player.queue.is_empty != True:
            player.queue.clear()
        if player.is_playing():
            await player.stop()
            await player.disconnect()
            await ctx.message.add_reaction("👍")
            return
        await player.disconnect()
        await ctx.message.add_reaction("👍")

    @commands.command(aliases=["sk","n","next"])
    async def skip(self, ctx:Context):
        """Skip the current song"""
        player: wavelink.Player = ctx.guild.voice_client
        if not player.is_playing():
            await ctx.reply("kya skip karu jab kuch nai baj raha",mention_author=False)
            return
        await player.stop()
        await ctx.reply("skip kardia bhai",mention_author=False)

    @commands.command(aliases=["q"])
    async def queue(self, ctx:Context):
        """Show the current queue"""
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
        player: wavelink.Player = ctx.guild.voice_client
        if not player.is_playing():
            await ctx.reply("kya dikhau jab kuch nai baj raha")
            return
        embed = discord.Embed(title="Now Playing", description=player.current.title, color=0x00ff00)
        #make emoji duration
        embed.set_image(url=player.current.thumbnail)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(aliases=["vol"])
    async def volume(self, ctx:Context, volume:int):
        """Change the volume"""
        player: wavelink.Player = ctx.guild.voice_client
        if volume > 100 or volume < 0:
            await ctx.reply("volume 0 se 100 ke beech me hona chahiye bhai")
            return
        await player.set_volume(volume)
        await ctx.reply(f"{volume} kardia volume",mention_author=False)



    
    




async def setup(bot):
    await bot.add_cog(Music(bot))