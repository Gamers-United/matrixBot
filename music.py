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
from config import settings as dsettings

class Music(commands.Cog):
    #initalization
    def __init__(self, bot):
        self.bot: discord.ext.commands.bot = bot
        self.pomice = pomice.NodePool()

    async def cog_load(self):
        await self.bot.wait_until_ready()
        await self.pomice.create_node(
            bot=self.bot,
            host=dsettings.lavalink_host,
            port=dsettings.lavalink_port,
            password=dsettings.lavalink_password,
            identifier=dsettings.lavalink_identifier,
            spotify_client_id=dsettings.spotify_client_id,
            spotify_client_secret=dsettings.spotify_client_secret
        )
        print("Music Module Is Setup & Ready")

    # Handle the listeners
    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: CustomPlayer, track: pomice.Track, _) -> None:
        await player.handleNextTrack()

    @commands.Cog.listener()
    async def on_pomice_track_stuck(self, player: CustomPlayer, track: pomice.Track, _):
        await player.handleNextTrack()
        try:
            await self.bot.get_channel(int(dsettings.channelid_error_log)).send(_)
        except Exception as e:
            print(e)
        await player.context.send(dsettings.song_stuck)
 
    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: CustomPlayer, track: pomice.Track, _) -> None:
        await player.context.send(dsettings.song_exception)
        try:
            await self.bot.get_channel(int(dsettings.channelid_error_log)).send(_)
        except Exception as e:
            print(e)
        await player.handleNextTrack()

    #commands
    @commands.command(aliases=["join", "j"])
    async def connect(self, ctx: commands.Context, channel: VoiceChannel = None) -> None:
        """ Joins the call """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send(dsettings.no_voice)
                return
        #setup the player
        player: CustomPlayer = await channel.connect(cls=CustomPlayer, self_deaf=True) 
        player.context = ctx
        await ctx.send(f"Connected to {channel.mention}")

    @commands.command(aliases=['dc','stop','leave'])
    async def disconnect(self, ctx: commands.Context) -> None:
        """ Disconnects the player from the voice channel and clears its queue. """
        player: CustomPlayer = ctx.voice_client
        if not ctx.voice_client:
            await ctx.send(dsettings.bot_connected)
            return
        elif ctx.author.voice.channel != player.channel:
            await ctx.send(dsettings.no_voice)
            return
        else:
            await player.destroy()
            await ctx.send(dsettings.bot_leave)

    @commands.command(aliases=['p'])
    async def play(self, ctx: discord.ext.commands.Context, *, query: str = None):
        """ Searches and plays a song from a given query. """
        player: CustomPlayer = ctx.voice_client
        if not player:
            await ctx.invoke(self.connect)
        player: CustomPlayer = ctx.voice_client
        
        if not player:
            #since we just tried to join, if it failed to join, then the person must not be in a accessible VC.
            return
        if player.is_paused == True and query is None:
            await player.set_pause(False)
            await ctx.send(dsettings.unpause)
            return
        #handle playing
        results = await player.get_tracks(query=query, ctx=ctx, search_type=pomice.SearchType.ytsearch)
        if not results:
            await ctx.send(dsettings.no_results)
            return

        if isinstance(results, pomice.Playlist):
            for track in results.tracks:
                await player.queue.put(track)
        elif len(results) == 1:
            await player.queue.put(results[0])
        else:
            # generate embed and send it out here
            itemListEmbed = discord.Embed(colour=discord.Colour.green(), title="Song Search Results")
            top5 = results[:5]
            for item in top5:
                itemListEmbed.add_field(name=(f"{str(results.index(item)+1)}. {str(item.title)} - {str(item.author)}"), value=str(item.info["uri"]), inline=False)

            #NEW -- Use buttons now
            buttons = buttonLIB.addSong(ctx=ctx)
            await ctx.send(embed=itemListEmbed, view=buttons)
            def check(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    return False
                else:
                    return True

            await self.bot.wait_for('interaction', check=check)
            selectionint = None
            for item in buttons.buttons:
                    if item.interacted == True:
                        selectionint = item.number

            a = ""
            for track in results:
                a += f"{track.title},{track.author}:"
            print(a)

            #process the selection to add to the track object.
            try:
                result = results[selectionint-1]
                await player.queue.put(result)
            except ValueError:
                await ctx.send(dsettings.search_invalid_selection)

        await ctx.send(dsettings.search_added_to_queue)
        #make sure the player is playing at this stage
        if not player.is_playing:
            await player.handleNextTrack()

    #managment commands
    @commands.command()
    async def skip(self, ctx, number: int = 1):
        player: CustomPlayer = ctx.voice_client
        if number == 1:
            await player.stop()
            await player.set_pause(False)
            await ctx.send(dsettings.skip_song)
        elif number > 1:
            if player.queue.count() < number:
                return await ctx.send(dsettings.skip_larger_than_queue)  
            for i in range(1,number):
                player.queue.pop()
            await player.stop()
            await player.set_pause(False)
            return await ctx.send("Removed first "+str(number)+" songs!")

    @commands.command()
    async def remove(self, ctx, index: int = 0):
        player: CustomPlayer = ctx.voice_client
        if player.queue.count() == 0:
            await ctx.send(dsettings.no_queue)
            return
        elif index > player.queue.count(): 
            await ctx.send(dsettings.remove_larger_than_queue)
            return
        elif index < 0:
            await ctx.send(dsettings.remove_out_of_bounds)
            return
        elif index == 0:
            await player.stop()
            return
        track = player.queue.__getitem__(index)
        player.queue.remove(track)
        title = track.info["title"]
        await ctx.send(f"Removed *{title}* from the queue.")

    @commands.command()
    async def queue(self, ctx, page: int = 1):
        await ctx.invoke(self.nowplaying)
        player: CustomPlayer = ctx.voice_client
        queue = player.queue.copy()
        songs = []
        for i in range(0, player.queue.count()):
            songs.append(queue.popleft())
        if len(songs) > 0 :
            pages = math.ceil(len(songs) / dsettings.items_per_page)
            start = (page - 1) * dsettings.items_per_page
            end = start + dsettings.items_per_page
            queue_list = ''
            time_remaining = 0
            for index, track in enumerate(songs[start:end], start=start):
                queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'
                time_remaining = time_remaining + track.length

            embed = discord.Embed(colour=discord.Color.blurple(), description=f'**{len(songs)} tracks**\n\n{queue_list}')
            #player current
            playerMinutes, playerSeconds = divmod((time_remaining/1000), 60)
            embed.set_footer(text=f'Viewing page {page}/{pages}! Time Remaining: {int(playerMinutes)}m{int(playerSeconds)}s')
            await ctx.send(embed=embed)

    @commands.command()
    async def shuffle(self, ctx):
        player: CustomPlayer = ctx.voice_client
        if player.queue.count() == 0:
            await ctx.send(dsettings.no_queue)
            return
        else:
            player.queue.shuffle()
        await ctx.send(dsettings.shuffle_complete)

    @commands.command()
    async def repeat(self, ctx):
        player: CustomPlayer = ctx.voice_client
        if player.is_repeating:
            player.stopRepeat()
            await ctx.send(dsettings.repeat_off)
        else:
            player.startRepeat()
            await ctx.send(dsettings.repeat_on)

    @commands.command()
    async def seek(self, ctx, time: str):
        player: CustomPlayer = ctx.voice_client
        if not player.is_playing:
            return await ctx.send(dsettings.not_playing)

        # Possible REGEX searches
        # HIGHEST TO LOWEST PRIORITY
        # FIND TYPE: <minutes>.<partial minutes> -- \n([0-9]\.[0-9]+)\n -- group contains e.g. 5.5, split by "." and times second part by 60.
        # FIND TYPE: <minutes>:<seconds> -- ([0-9]+:[0-9]+) -- group contains e.g. 5:30, split by ":"
        # FIND TYPE: <minutes>M+<seconds> -- ([0-9\.]+([ms]| [ms])) -- for each match, group 1 is value, group 2 is unit (possibly including a \n)
        # IF NOTHING ELSE MATCHES. INTERPRET AS SECONDS BY ITSELF -- \n([0-9]+\n)
        # OTHERWISE ERROR
        time_dict = {"m": 60, "s": 1}

        ## CASE 1
        try:
            t = re.search("([0-9]\.[0-9]+)", time)
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
                passadd_field
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
            await ctx.send(dsettings.seek_invalid_time)
            return

        #seek the player
        print(time)
        await player.seek(float(time*1000))
        await ctx.send(f'Moved track to **{str(datetime.timedelta(seconds=int(time)))}**')
 
    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx):
        player: CustomPlayer = ctx.voice_client
        song = 'Nothing'
        if player.current is None:
            await ctx.send(dsettings.not_playing)
            return
        if player.current.is_stream:
            dur = 'LIVE'
        else:
            #player current
            playerMinutes, playerSeconds = divmod((player.position/1000), 60)
            #song total
            songMinutes, songSeconds = divmod((player.current.length/1000), 60)
            #format string
            channelurl = player.current.info["channeluri"]
            dur = f"{str(int(playerMinutes))}:{str(int(playerSeconds))} out of {str(int(songMinutes))}:{str(int(songSeconds))}"
            song = f'**[{player.current.title}]({player.current.uri})** | **[{player.current.author}]({channelurl})**\n{dur}'
        embed = discord.Embed(colour=discord.Color.dark_red(), title=dsettings.now_playing_title, description=song)
        await ctx.send(embed=embed)

    @commands.command()
    async def pause(self, ctx):
        player: CustomPlayer = ctx.voice_client
        if player.is_paused:
            await ctx.send(dsettings.already_paused)
        else:
            await player.set_pause(True)
            await ctx.send(dsettings.paused)

    @commands.command(aliases=['unpause'])
    async def resume(self, ctx):
        player: CustomPlayer = ctx.voice_client
        if player.is_paused:
            await ctx.send(dsettings.unpaused)
            await player.set_pause(False)

    #filters
    @commands.command(aliases=['setFilter', 'newFilter'])
    async def filter(self, ctx):
        await ctx.send(view=buttonLIB.filterButtons(ctx=ctx))

    @commands.command(aliases=['v'])
    async def volume(self, ctx, level: int):
        player: CustomPlayer = ctx.voice_client
        if level > 500:
            await ctx.send(dsettings.volume_too_high)
        elif level < 0:
            await ctx.send(dsettings.volume_too_low)
        else:
            await player.set_volume(level)
            await ctx.send(f"Set volume to {level}%")

    @commands.command(aliases=['removeFilter', 'rFilter'])
    async def delfilter(self,ctx):
        await ctx.send(view=buttonLIB.deleteFilterButtons(ctx))

    #lyrics
    @commands.command()
    async def lyrics(self, ctx):
        player: CustomPlayer = ctx.voice_client
        results = Lyrics.SearchForLyrics(player.current.title)
        if len(results) == 0:
            await ctx.send(dsettings.lyrics_not_found)
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

    #suggested playlists
    @commands.command(aliases=["suggested", "sp", "playlists", "suggest"])
    async def suggestedPlaylists(self, ctx):
        playlistembed = discord.Embed(colour=discord.Color.gold(), title=dsettings.suggested_playlists_title, description=dsettings.suggested_playlists_description)
        playlistembed.add_field(inline=False, name=dsettings.playlist_1_name, value=dsettings.playlist_1_artists)
        playlistembed.add_field(inline=False, name=dsettings.playlist_2_name, value=dsettings.playlist_2_artists)
        playlistembed.add_field(inline=False, name=dsettings.playlist_3_name, value=dsettings.playlist_3_artists)
        playlistembed.add_field(inline=False, name=dsettings.playlist_4_name, value=dsettings.playlist_4_artists)
        playlistembed.add_field(inline=False, name=dsettings.playlist_5_name, value=dsettings.playlist_5_artists)
        playlistembed.add_field(inline=False, name=dsettings.playlist_6_name, value=dsettings.playlist_6_artists)
        playlistembed.add_field(inline=False, name=dsettings.playlist_7_name, value=dsettings.playlist_7_artists)
        playlistembed.add_field(inline=False, name=dsettings.playlist_8_name, value=dsettings.playlist_8_artists)
        await ctx.send(embed=playlistembed, view=buttonLIB.playlistPlayer(ctx=ctx, music=self))

async def setup(bot):
    await bot.add_cog(Music(bot))