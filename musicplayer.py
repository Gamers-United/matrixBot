#  Copyright 2023 Macauley Lim xmachd@gmail.com
#  This code is licensed under GNU AFFERO GENERAL PUBLIC LICENSE v3.0.
#  A copy of this license should have been provided with the code download, if not see https://www.gnu.org/licenses/
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU AGPL v3.0 for more details.

import datetime
import re
from contextlib import suppress

import discord
import googleapiclient.discovery
import googleapiclient.errors
import pomice
import spotipy
from discord import VoiceChannel, Colour, Message
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials

from config import settings as dsettings


class CustomPlayer(pomice.Player):
    """Custom player class"""

    def __init__(self, bot: commands.Bot, channel: VoiceChannel) -> None:
        super().__init__(bot, channel)
        self.queue = pomice.Queue()
        self.context: commands.Context = None
        self.np: discord.Message = None
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=dsettings.google_api_key)
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(client_id=dsettings.spotify_client_id,
                                                                client_secret=dsettings.spotify_client_secret))

    # handle the next track
    async def handleNextTrack(self) -> Message | None:
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
        if track.track_type == pomice.TrackType.YOUTUBE:
            code = re.search("https:\/\/www\.youtube\.com\/watch\?v=(.+)", track.uri).group(1)
            request = self.youtube.videos().list(part="snippet", id=code)
            response = request.execute()
            responset = response["items"][0]["snippet"]["channelId"]
            track.info["channeluri"] = f"https://youtube.com/channel/{responset}"
            channelurl = track.info["channeluri"]
            if channelurl is not None:
                return await self.context.send(embed=discord.Embed(title=dsettings.now_playing_title,
                                                                   description=f"**[{track.title}]({track.uri})** | **[{track.author}]({channelurl})**",
                                                                   colour=Colour.dark_red(),
                                                                   timestamp=datetime.datetime.now()))
            else:
                return await self.context.send(embed=discord.Embed(title=dsettings.now_playing_title,
                                                                   description=f"**[{track.title}]({track.uri})** | **{track.author}**",
                                                                   colour=Colour.dark_red(),
                                                                   timestamp=datetime.datetime.now()))
        elif track.track_type == pomice.TrackType.SPOTIFY:
            result = self.spotify.track(re.search("https:\/\/open\.spotify\.com\/track\/(.+)", track.uri).group(1),
                                        "AU")
            artisturl = result["artists"][0]["external_urls"]["spotify"]
            return await self.context.send(embed=discord.Embed(title=dsettings.now_playing_title,
                                                               description=f"**[{track.title}]({track.uri})** | **[{track.author}]({artisturl}) | [YT]({track.original.uri})**",
                                                               colour=Colour.dark_red(),
                                                               timestamp=datetime.datetime.now()))
        else:
            return await self.context.send(embed=discord.Embed(title=dsettings.now_playing_title,
                                                               description=f"**[{track.title}]({track.uri})** | **{track.author}**",
                                                               colour=Colour.dark_red(),
                                                               timestamp=datetime.datetime.now()))

    async def exit(self):
        """closes the player down in the guild"""
        with suppress(discord.HTTPException, KeyError):
            await self.destroy()
