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
import googleapiclient.discovery
import googleapiclient.errors

class CustomPlayer(pomice.Player):
    """Custom player class"""
    def __init__(self, bot: commands.Bot, channel: VoiceChannel) -> None:
        super().__init__(bot, channel)
        self.queue = pomice.Queue()
        self.context: commands.Context = None
        self.np: discord.Message = None
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=dsettings.google_api_key)

    # handle the next track
    async def handleNextTrack(self) -> None:
        """Handles the next track playing, and now playing prompt with context"""
        try:
            try:
                track: pomice.Track = self.queue.get()
            except pomice.exceptions.QueueEmpty:
                return await self.exit()
            await self.play(track)
        except Exception as e:
            print(e)
            return await self.exit()
        print(f"{type(track)};{track.author};{track.ctx};{track.identifier};{track.info};{track.is_seekable};{track.is_stream};{track.isrc};{track.length};{track.original};{track.position};{track.requester};{track.spotify};{track.spotify_track};{track.thumbnail};{track.title};{track.track_id};{track.uri}")
        if (track.uri != None):
            code = re.search("https:\/\/www\.youtube\.com\/watch\?v=(.+)", track.uri).group(1)
            request = self.youtube.videos().list(part="snippet", id=code)
            response = request.execute()
            responset = response["items"][0]["snippet"]["channelId"]
            track.info["channeluri"] = f"https://youtube.com/channel/{responset}"
            channelurl = track.info["channeluri"]
            return await self.context.send(embed=discord.Embed(title=dsettings.now_playing_title, description=f"**[{track.title}]({track.uri})** | **[{track.author}]({channelurl})**", colour=Colour.dark_red(), timestamp=datetime.datetime.now()))
        else:
             return await self.context.send(embed=discord.Embed(title=dsettings.now_playing_title, description=f"**[{track.title}]({track.uri})** | **[{track.author}]**", colour=Colour.dark_red(), timestamp=datetime.datetime.now()))

    async def exit(self):
        """closes the player down in the guild"""
        with suppress((discord.HTTPException), (KeyError)):
            await self.destroy()