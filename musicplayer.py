import re
import discord
import pomice
import math
import asyncio
from discord.ext import commands
from discord import VoiceChannel, Embed, Colour
from lyrics import Lyrics
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type, Union
from contextlib import suppress
import datetime

class CustomPlayer(pomice.Player):
    """Custom player class"""
    def __init__(self, bot: commands.Bot, channel: VoiceChannel) -> None:
        super().__init__(bot, channel)
        self.queue = asyncio.Queue()
        self.context: commands.Context = None
        self.np: discord.Message = None

    # handle the next track
    async def handleNextTrack(self) -> None:
        """Handles the next track playing, and now playing prompt with context"""
        if self.np:
            with supress(discord.HTTPException):
                await self.controller.delete()
        
        try:
            track: pomice.Track = self.queue.get_nowait()
        except asyncio.QueueEmpty:
            return await self.exit()

        await self.play(track)

        if track.is_stream:
            await self.context.send(embed=discord.Embed(title="Now Playing Live:", description=f"{track.title}", url=track.uri, colour=Colour.green(), timestamp=datetime.datetime.now()))
        else:
            await self.context.send(embed=discord.Embed(title="Now Playing:", description=f"{track.title}", url=track.uri, colour=Colour.green(), timestamp=datetime.datetime.now()))

    async def exit(self):
        """closes the player down in the guild"""
        with suppress((discord.HTTPException), (KeyError)):
            await self.destroy()
            if self.controller:
                await self.controller.delete()

    async def addContext(self, ctx: commands.Context):
        """Add a context variable for now playing messages"""
        self.context = ctx