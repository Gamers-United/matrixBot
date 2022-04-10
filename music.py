import re
import discord
import pomice
import math
import asyncio
from discord.ext import commands
from discord import VoiceChannel, Embed, Colour
from lyrics import Lyrics
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type, Union
import datetime
import buttonLIB
from musicplayer import CustomPlayer

url_rx = re.compile(r'https?://(?:www\.)?.+')
time_rx = re.compile('[0-9]+')

# class YoutubeMusicPlaylist(lavapy=):
#     _trackCls: Type[lavapy.Track] = lavapy.YoutubeMusicTrack

#     def __repr__(self) -> str:
#         return f"<Lavapy YoutubeMusicPlaylist (Name={self.name}) (Track count={len(self.tracks)})>"

class Music(commands.Cog):
    #initalization
    def __init__(self, bot):
        self.bot: discord.ext.commands.bot = bot
        self.pomice = pomice.NodePool()
    
    async def cog_load(self):
        await self.bot.wait_until_ready()
        await self.pomice.create_node(
            bot=self.bot,
            host="10.100.1.56",
            port="19999",
            password="mltechmaynotpassthispointwithoutpermission",
            identifier="Main",
            spotify_client_id="0de30a1427ad404f877dd2ef005942ba",
            spotify_client_secret="c63891d0313442489e39aeb05419f209"
        )
        print("Lavalink Is Setup & Ready")

    # Handle the listeners
    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: CustomPlayer, track: pomice.Track, _) -> None:
        await player.handleNextTrack()

    @commands.Cog.listener()
    async def on_pomice_track_stuck(self, player: CustomPlayer, track: pomice.Track, _):
        await player.handleNextTrack()
    
    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: CustomPlayer, track: pomice.Track, _) -> None:
        await player.handleNextTrack()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        # guild_check = ctx.guild is not None
        # if guild_check:
        #     await self.ensure_voice(ctx)
        # return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("An error has occured!\n"+str(error))

    #commands
    @commands.command(aliases=["join", "j"])
    async def connect(self, ctx: commands.Context, channel: VoiceChannel = None) -> None:
        """ Joins the call """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send("You must be in a voice channel in order to use the join command.")
                return
        #setup the player
        player: CustomPlayer = await channel.connect(cls=CustomPlayer)
        player.context = ctx
        await ctx.guild.change_voice_state(channel=channel,self_deaf=True)
        await ctx.send(f"Connected to {channel.mention}")

    @commands.command(aliases=['dc','stop','leave'])
    async def disconnect(self, ctx: commands.Context) -> None:
        """ Disconnects the player from the voice channel and clears its queue. """
        player: CustomPlayer = ctx.voice_client
        if not ctx.voice_client:
            await ctx.send("The bot must be connected to use this command.")
            return
        elif ctx.author.voice.channel != player.channel:
            await ctx.send("You must be in the active voice channel to use this command.")
            return
        else:
            await player.destroy()
            await ctx.send("The bot has left the channel.")

    @commands.command(aliases=['p'])
    async def play(self, ctx: discord.ext.commands.Context, *, query: str = None):
        """ Searches and plays a song from a given query. """
        player: CustomPlayer = ctx.voice_client
        if not player:
            await ctx.invoke(self.connect)
        if player.is_paused == True and query is None:
            await player.set_pause(False)
            await ctx.send("Unpausing player!")
            return
        if not player:
            #since we just tried to join, if it failed to join, then the person must not be in a accessible VC.
            await ctx.send("You are not in a voice channel.")
            return
        #handle playing
        results = await player.get_tracks(query=query, ctx=ctx, search_type=pomice.SearchType.ytmsearch)

        if not results:
            await ctx.send("No results were found")
            return
        if isinstance(results, pomice.Playlist):
            for track in results.tracks:
                await player.queue.put(track)
        elif len(reuslts) == 1:
            await player.queue.put(results[0])
        else:
            # generate embed and send it out here
            itemListEmbed = discord.Embed(colour=discord.Color.blurple(), title="Song Search Results", description="Type number in chat for correct song")
            top5 = result[:5]
            for item in top5:
                itemListEmbed.add_field(name=(str(result.index(item)+1)+". "+str(item.info["title"])), value=str(item.info["uri"]), inline=False)
            await ctx.send(embed=itemListEmbed)

            #await for response
            def check(m):
                return ctx.author == m.author
        
            selection = await self.bot.wait_for('message', check=check)
            #process the selection to add to the track object.
            try:
                selectionint = int(selection.content)-1
                result = result[selectionint]
            except ValueError:
                await ctx.send("Invalid selection")
        #make sure the player is playing at this stage
        if not player.is_playing:
            await player.handleNextTrack()

    #managment commands
    @commands.command()
    async def skip(self, ctx, number: int = 1):
        player: CustomPlayer = ctx.voice_client
        if number == 1:
            await player.stop()
            await ctx.send("Song skipped!")
        elif number > 1:
            if player.queue.qsize() < number:
                return await ctx.send("Requested to skip more songs than in queue!")  
            for i in range(1,number):
                player.queue.get_nowait()
            return await ctx.send("Removed first "+str(number)+" songs!")

    @commands.command()
    async def remove(self, ctx, index: int):
        player: CustomPlayer = ctx.voice_client
        if player.queue.qsize() == 0:
            await ctx.send('Nothing queued!')
            return
        elif index > player.queue.qsize(): 
            await ctx.send('Can not remove a song past the number of songs in queue!')
            return
        elif index < 1:
            await ctx.send("Song to remove must have an index higher than or equal to 1.")
            return
        elif index == 1:
            await player.stop()
        index = index - 1
        #rotate the queue so that the song can be popped from the left hand side, and then rotate back.
        player.queue._queue.rotate(index)
        removed = player.queue._queue.pop()
        player.queue._queue.rotate((index * -1))
        title = removed.info["title"]
        await ctx.send(f"Removed *{title}* from the queue.")

    @commands.command()
    async def queue(self, ctx, page: int = 1):
        player: CustomPlayer = ctx.voice_client
        queue = player.queue._queue.copy()
        songs = []
        for i in range(1, player.queue.qsize()):
            songs.append(player.queue._queue.pop())

        #probably should eventually be moved into the config?
        items_per_page = 10
        pages = math.ceil(len(songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''
        for index, track in enumerate(songs[start:end], start=start):
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'

        embed = discord.Embed(colour=discord.Color.blurple(), description=f'**{len(songs)} tracks**\n\n{queue_list}')
        embed.set_footer(text=f'Viewing page {page}/{pages}!')
        await ctx.send(embed=embed)
    
    @commands.command()
    async def shuffle(self, ctx):
        player: CustomPlayer = ctx.voice_client
        if len(player.queue.tracks) == 0:
            await ctx.send("No tracks to shuffle!")
            return
        else:
            player.queue.shuffle()
        await ctx.send(f"Shuffled the queue")

    @commands.command()
    async def repeat(self, ctx):
        player: CustomPlayer = ctx.voice_client
        if player.isRepeating:
            player.stopRepeat()
            await ctx.send("Stopped repeating player!")
        else:
            player.startRepeat()
            await ctx.send("Started repeating player!")

    @commands.command()
    async def seek(self, ctx, time: str):
        player: CustomPlayer = ctx.voice_client
        if not player.isPlaying:
            return await ctx.send('Nothing playing!')

        # Possible REGEX searches
        # HIGHEST TO LOWEST PRIORITY
        # FIND TYPE: <minutes>.<partial minutes> -- \n([0-9]\.[0-9]+)\n -- group contains e.g. 5.5, split by "." and times second part by 60.
        # FIND TYPE: <minutes>:<seconds> -- ([0-9]+:[0-9]+) -- group contains e.g. 5:30, split by ";"
        # FIND TYPE: <minutes>M+<seconds> -- ([0-9\.]+([ms]| [ms])) -- for each match, group 1 is value, group 2 is unit (possibly including a \n)
        # IF NOTHING ELSE MATCHES. INTERPRET AS SECONDS BY ITSELF -- \n([0-9]+\n)
        # OTHERWISE ERROR
        time_dict = {"m": 60, "s": 1}

        ## CASE 1
        try:
            t = re.search("\n([0-9]\.[0-9]+)\n", time)
            time = int(float(t.group(1)) * 60)
        except:
            pass
            # I guess it's not this format...

        ## CASE 2
        try:
            t = re.search("([0-9]+:[0-9]+)", time)
            r = t.group(1).split(":")
            time = (int(r[0]) * 60) + int(r[1])
        except:
            pass
            # I guess it's not this format...

        ## CASE 3
        try:
            t = re.findall("([0-9\.]+([ms]| [ms]))", time)
            ovalue = int(t[0].group(1))
            otype = t[0].group(2)
            otime = ovalue * time_dict[otype]
            try:
                tvalue = int(t[1].group(1))
                ttype = t[1].group(2)
                ttime = tvalue * time_dict[ttype]
            except:
                pass
                # I guess this only contains either minutes or seconds...
            time = otime + ttime
        except:
            pass
            # I guess it's not this format...
        
        ## CASE 4
        try:
            t = re.search("\n([0-9]+\n)", time)
            time = int(t.group(1).strip("\n"))
        except:
            pass
            # I guess it's not this format...
        
        if time is None:
            await ctx.send("Invalid time")
            return

        #seek the player
        await player.seek(int(time))
        await ctx.send(f'Moved track to **{str(datetime.timedelta(seconds=int(time)))}**')

    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx):
        player: CustomPlayer = ctx.voice_client
        song = 'Nothing'
        if player.track is None:
            await ctx.send("Nothing playing... Play something now with !play")
            return
        if player.track.isStream:
            dur = 'LIVE'
        else:
            #player current
            playerMinutes, playerSeconds = divmod(player.position, 60)
            #song total
            songMinutes, songSeconds = divmod(player.track.length, 60)
            #format string
            dur = f"{str(playerMinutes)}:{str(playerSeconds)} out of {str(songMinutes)}:{str(songSeconds)}"
            song = f'**[{player.track.title}]({player.track.uri})**\n({dur})'
        embed = discord.Embed(colour=discord.Color.blurple(), title='Now Playing', description=song)
        await ctx.send(embed=embed)

    @commands.command()
    async def pause(self, ctx):
        player: CustomPlayer = ctx.voice_client
        if player.is_paused:
            await ctx.send("Player already paused!")
        else:
            await player.pause()
            await ctx.send("Player paused!")
    
    @commands.command(aliases=['unpause'])
    async def resume(self, ctx):
        player: CustomPlayer = ctx.voice_client
        if player.is_paused:
            await ctx.send("Unpausing player!")
            await player.resume()

    #filters
    @commands.command()
    async def setFilter(self, ctx):
        await ctx.send(view=buttonLIB.filterButtons(ctx=ctx))

    @commands.command()
    async def volume(self, ctx, level: int):
        player: CustomPlayer = ctx.voice_client
        if level > 1000:
            await ctx.send("Volume too high!")
        elif level < 0:
            await ctx.send("Volume too low!")
        else:
            await player.setVolume(level/2)
            await ctx.send(f"Set volume to {level/2}%")

    @commands.command()
    async def deleteFilter(self,ctx):
        await ctx.send(view=buttonLIB.deleteFilterButtons(ctx))

    #lyrics
    @commands.command()
    async def lyrics(self, ctx):
        player: CustomPlayer = ctx.voice_client
        results = Lyrics.SearchForLyrics(player.track.title)
        if len(results) == 0:
            await ctx.send("No Lyrics Found")
        else:
            await ctx.send(embed=Lyrics.GenerateEmbed(results))
            def check(message):
                return message.author == ctx.author
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            selection = int(msg.content) - 1
            lyr = Lyrics.lyrics_from_song_api_path(results[selection]["result"]["api_path"])
            if(len(lyr)>4095):
                n=4095
                chunks = [lyr[i:i+n] for i in range(0, len(lyr), n)]
                for item in chunks:
                    if chunks.index(item) == 0:
                        final = discord.Embed(colour=discord.Color.blurple(), title="Lyrics for "+str(results[selection]["result"]["full_title"]), description=item)
                        await ctx.send(embed=final)
                    else:
                        final = discord.Embed(colour=discord.Color.blurple(), title="Lyrics for "+str(results[selection]["result"]["full_title"]+" Continued"), description=item)
                        await ctx.send(embed=final)
            else:
                final = discord.Embed(colour=discord.Color.blurple(), title="Lyrics for "+str(results[selection]["result"]["full_title"]), description=lyr)
                await ctx.send(embed=final)

async def setup(bot):
    await bot.add_cog(Music(bot))