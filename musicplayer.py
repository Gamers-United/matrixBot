import re
import discord
import lavapy
from lavapy.ext import spotify
import math
import asyncio
from discord.ext import commands
from discord import VoiceChannel, Embed, Colour
from lyrics import Lyrics
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type, Union

class CustomPlayer(lavapy.Player):
    """Custom lavapy Player class"""
    def __init__(self, bot: commands.Bot, channel: VoiceChannel) -> None:
        super().__init__(bot, channel)
        self.context: Optional[commands.Context] = None

    # handle the next track
    async def playNext(self) -> None:
        if self.queue.isEmpty:
            await self.context.send("Queue is complete. Disconnecting.")
            await self.destroy()
        else:
            await self.play(self.queue.next())
