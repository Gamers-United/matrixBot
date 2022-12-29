import discord.opus
import sys
from discord import opus
from discord.ext import commands

if 'linux' in sys.platform:
    opus.load_opus('opus')

import pyVBAN
import pyaudio


class DJReceiver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def helpVBAN(self, ctx):
        await ctx.send("""To Connect to VBAN:
- Port in use must be 6020 UDP
- IP address to connect to is 103.48.200.23
- 2 Channel Format in PCM 16 bits @ 48KHz
- Specify IP & stream name in command:
!PlayVBAN <source ip> <stream name>
Where source IP must be public IP if behind NAT.
Send stream before running command.""")

    @commands.command()
    async def PlayVBAN(self, ctx, ip: str, stream_name: str):
        await ctx.send(f"Attempting to play VBAN Stream with ip: {ip}, Name: {stream_name}")
        cl = pyVBAN.VBAN_Recv(ip, stream_name, 6020, None)
        cl.runonce()

        voice = await ctx.author.voice.channel.connect()
        if not voice:
            await ctx.send("Use this command while in a voice channel.")
        voice.play(discord.PCMAudio(cl.stream))


async def setup(bot: commands.Bot):
    await bot.add_cog(DJReceiver(bot))
