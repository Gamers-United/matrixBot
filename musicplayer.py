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
from config import settings as dsettings

class CustomPlayer(pomice.Player):
    """Custom player class"""
    def __init__(self, bot: commands.Bot, channel: VoiceChannel) -> None:
        super().__init__(bot, channel)
        self.queue = asyncio.Queue()
        self.context: commands.Context = None
        self.np: discord.Message = None
        self.is_repeating = False
        self.repeatedTrack: pomice.Track = None

    # handle the next track
    async def handleNextTrack(self) -> None:
        """Handles the next track playing, and now playing prompt with context"""
        if self.is_repeating:
            await self.play(self.repeatedTrack)
            return
        
        try:
            try:
                track: pomice.Track = self.queue.get_nowait()
            except asyncio.QueueEmpty:
                return await self.exit()

            await self.play(track)
        except Exception as e:
            print(e)
        await self.context.send(embed=discord.Embed(title=dsettings.now_playing_title, description=f"**[{track.title}]({track.uri})**", colour=Colour.dark_red(), timestamp=datetime.datetime.now()))

    async def stopRepeat(self):
        self.is_repeating = False
        self.repeatedTrack = None

    async def startRepeat(self):
        self.is_repeating = True
        self.repeatedTrack = self.current

    async def exit(self):
        """closes the player down in the guild"""
        with suppress((discord.HTTPException), (KeyError)):
            await self.destroy()