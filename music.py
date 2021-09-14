import re
import discord
import lavalink
from discord.ext import commands

url_rx = re.compile(r'https?://(?:www\.)?.+')

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
            await ctx.send(error.original)

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
        if not url_rx.match(query):
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
            embed.title = 'Track Queued'
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
        await ctx.send(embed=embed)
        if not player.is_playing:
            await player.play()

    @commands.command(aliases=['dc'])
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
    
    @commands.command()
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