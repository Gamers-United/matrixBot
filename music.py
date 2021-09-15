import re
import discord
import lavalink
import math
from discord.ext import commands

url_rx = re.compile(r'https?://(?:www\.)?.+')
time_rx = re.compile('[0-9]+')

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(832975268825006090)
            bot.lavalink.add_node('10.100.1.56', 2333, 'mltechmaynotpassthispointwithoutpermission', 'eu', 'default-node')
            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')
        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("An error has occured!")

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandInvokeError('Join a voicechannel first.')

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError('Not connected.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            player.store('channel', ctx.channel.id)
            await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_deaf=True)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError('You need to be in my voicechannel.')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            await guild.change_voice_state(channel=None)

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        #move on to query
        query = query.strip('<>')
        query_type = str(query[:2])
        print("DEBUG+QUERYID+"+str(query)+"|"+str(query[:2]))
        if not url_rx.match(query):
            if query_type == "sc:":
                query = f'scsearch:{query}'
            elif query_type == "yt:":
                query = f'ytsearch:{query}'
            else:
                query = f'ytsearch:{query}'
        results = await player.node.get_tracks(query)
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!')

        embed = discord.Embed(color=discord.Color.blurple())
        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
            embed.title = 'Playlist Queued!'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
        else:
            track = results['tracks'][0]
            embed.title = 'Track Queued!'
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
        await ctx.send(embed=embed)
        if not player.is_playing:
            await player.play()

    @commands.command()
    async def skip(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await player.skip()
        await ctx.send("Song skipped!")

    @commands.command()
    async def remove(self, ctx, index: int):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send('Nothing queued!')
        if index > len(player.queue) or index < 1:
            return await ctx.send('Song to remove must be more than one and less than the queue length!')
        index = index - 1
        removed = player.queue.pop(index)
        await ctx.send('Removed *' + removed.title + '* from the queue.')

    @commands.command()
    async def queue(self, ctx, page: int = 1):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''
        for index, track in enumerate(player.queue[start:end], start=start):
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'

        embed = discord.Embed(colour=discord.Color.blurple(), description=f'**{len(player.queue)} tracks**\n\n{queue_list}')
        embed.set_footer(text=f'Viewing page {page}/{pages}!')
        await ctx.send(embed=embed)

    @commands.command()
    async def seek(self, ctx, time):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('Not playing.')
        pos = '+'
        if time.startswith('-'):
            pos = '-'
        seconds = time_rx.search(time)
        if not seconds:
            return await ctx.send('You need to specify the amount of seconds to skip!')
        seconds = int(seconds.group()) * 1000
        if pos == '-':
            seconds = seconds * -1
        track_time = player.position + seconds
        await player.seek(track_time)
        await ctx.send(f'Moved track to **{lavalink.format_time(track_time)}**')

    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        song = 'Nothing'
        if player.current:
            pos = lavalink.format_time(player.position)
            if player.current.stream:
                dur = 'LIVE'
            else:
                dur = lavalink.format_time(player.current.duration)
            song = f'**[{player.current.title}]({player.current.uri})**\n({pos}/{dur})'
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Now Playing', description=song)
        await ctx.send(embed=embed)

    @commands.command(aliases=['dc','stop'])
    async def disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            return await ctx.send('Not connected.')
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('You\'re not in my voicechannel!')
        player.queue.clear()
        await player.stop()
        await ctx.guild.change_voice_state(channel=None)
        await ctx.send('*⃣ | Disconnected.')
    
    @commands.command()
    async def volume(self, ctx, level: int):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if level > 200:
            await ctx.send("Volume too high!")
        elif level < 1:
            await ctx.send("Volume too low!")
        else:
            await player.set_volume(level)
            await ctx.send("Set volume to "+str(level)+"!")
    
    @commands.command()
    async def pause(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.paused:
            await ctx.send("Player already paused!")
        else:
            await player.set_pause(True)
            await ctx.send("Player paused!")
    
    @commands.command(aliases=['unpause'])
    async def resume(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        #check for resume
        if player.paused:
            await ctx.send("Unpausing player!")
            await player.set_pause(False)


    @commands.command()
    async def eq(self, ctx, band: int, level: float):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if level > 1:
            await ctx.send("Level out of bounds -0.25 to 1.00.")
        elif level < -0.25:
            await ctx.send("Level out of bounds -0.25 to 1.00.")
        elif band < 0:
            await ctx.send("Band out of bounds 0 to 14.")
        elif band > 14:
            await ctx.send("Band out of bounds 0 to 14.")
        else:
            await player.set_gain(band, level)
            await ctx.send("Set band "+str(band)+" to "+str(level)+".")

    @commands.command()
    async def reseteq(self,ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await player.reset_equalizer()
        await ctx.send("EQ Reset!")

def setup(bot):
    bot.add_cog(Music(bot))