#  Copyright 2023 Macauley Lim xmachd@gmail.com
#  This code is licensed under GNU AFFERO GENERAL PUBLIC LICENSE v3.0.
#  A copy of this license should have been provided with the code download, if not see https://www.gnu.org/licenses/
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU AGPL v3.0 for more details.

import discord
import pomice
from discord.ext import commands

from config import settings as dsettings
from musicplayer import CustomPlayer

filterOptions = [
    discord.SelectOption(label="Select Filter", default=True),
    discord.SelectOption(label="Equalizer"),
    discord.SelectOption(label="Karaoke"),
    discord.SelectOption(label="Timescale"),
    discord.SelectOption(label="Tremolo"),
    discord.SelectOption(label="Vibrato"),
    discord.SelectOption(label="Rotation"),
    discord.SelectOption(label="Distortion"),
    discord.SelectOption(label="ChannelMix"),
    discord.SelectOption(label="Low Pass"),
]

equalizerBandOptions = [
    discord.SelectOption(label="Band 1 (Lowest)", default=True, value="0"),
    discord.SelectOption(label="Band 2", value="1"),
    discord.SelectOption(label="Band 3", value="2"),
    discord.SelectOption(label="Band 4", value="3"),
    discord.SelectOption(label="Band 5", value="4"),
    discord.SelectOption(label="Band 6", value="5"),
    discord.SelectOption(label="Band 7", value="6"),
    discord.SelectOption(label="Band 8", value="7"),
    discord.SelectOption(label="Band 9", value="8"),
    discord.SelectOption(label="Band 10", value="9"),
    discord.SelectOption(label="Band 11", value="10"),
    discord.SelectOption(label="Band 12", value="11"),
    discord.SelectOption(label="Band 13", value="12"),
    discord.SelectOption(label="Band 14", value="13"),
    discord.SelectOption(label="Band 15 (Highest)", value="14"),
]

equalizerBandGains = [
    discord.SelectOption(label="-25%", value="-0.25"),
    discord.SelectOption(label="0%", default=True, value="0.0"),
    discord.SelectOption(label="+25%", value="0.25"),
    discord.SelectOption(label="+50%", value="0.5"),
    discord.SelectOption(label="+75%", value="0.75"),
    discord.SelectOption(label="+100%", value="1.0")
]

noOptions = [
    discord.SelectOption(label="N/A", default=True)
]

filterArgumentOptions = {
    "Equalizer": [["Band Options", equalizerBandOptions], ["Band Gain", equalizerBandGains], ["N/A", noOptions],
                  ["N/A", noOptions]],
}


class filterButtons(discord.ui.View):
    def __init__(self, *, timeout=120, ctx: discord.ext.commands.Context):
        super().__init__(timeout=timeout)
        self.ctx = ctx

    @discord.ui.select(placeholder="Select Filter", options=filterOptions)
    async def eqButton(self, select: discord.ui.select, interaction: discord.Interaction):
        await self.ctx.send(view=filterButtonsOptions(ctx=self.ctx, setup=filterArgumentOptions[interaction.values[0]],
                                                      strtype=interaction.values[0]))
        await interaction.response.defer()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return False
        else:
            return True

    async def on_timeout(self):
        await self.ctx.send("Timed out!")


class deleteFilterButtons(discord.ui.View):
    def __init__(self, *, timeout=120, ctx: discord.ext.commands.Context):
        super().__init__(timeout=timeout)
        self.ctx = ctx

    @discord.ui.select(placeholder="Select Filter to Delete", options=filterOptions)
    async def eqButton(self, select: discord.ui.select, interaction: discord.Interaction):
        player: CustomPlayer = self.ctx.voice_client
        eq = pomice.filters.Equalizer(levels=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        await interaction.response.defer()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return False
        else:
            return True

    async def on_timeout(self):
        await self.ctx.send("Timed out!")


class filterButtonsOptions(discord.ui.View):
    def __init__(self, *, timeout=120, ctx: discord.ext.commands.Context, setup: list, strtype: str):
        super().__init__(timeout=timeout)
        self.valuea = None
        self.valueb = None
        self.valuec = None
        self.valued = None
        self.ctx = ctx
        self.viewa = setup[0][0]
        self.viewb = setup[1][0]
        self.viewc = setup[2][0]
        self.viewd = setup[3][0]
        self.opta = setup[0][1]
        self.optb = setup[1][1]
        self.optc = setup[2][1]
        self.optd = setup[3][1]
        self.type = strtype
        self.selectora = discord.ui.select(placeholder=self.viewa, options=self.opta)(self.selectorA)
        self.selectorb = discord.ui.select(placeholder=self.viewb, options=self.optb)(self.selectorB)
        self.selectorc = discord.ui.select(placeholder=self.viewc, options=self.optc)(self.selectorC)
        self.selectord = discord.ui.select(placeholder=self.viewd, options=self.optd)(self.selectorD)

    async def selectorA(self, select: discord.ui.select, interaction: discord.Interaction):
        self.valuea = select.value

    async def selectorB(self, select: discord.ui.select, interaction: discord.Interaction):
        self.valueb = select.value

    async def selectorC(self, select: discord.ui.select, interaction: discord.Interaction):
        self.valuec = select.value

    async def selectorD(self, select: discord.ui.select, interaction: discord.Interaction):
        self.valued = select.value

    @discord.ui.button()
    async def submitButton(self, button: discord.ui.button, interaction: discord.Interaction):
        player: CustomPlayer = self.ctx.voice_client
        if self.type == "Equalizer":
            if player.filter is None:
                eq = pomice.filters.Equalizer(levels=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            else:
                eq = player.filters["Equalizer"]
            eq.levels[int(self.valuea)] = float(self.valueb)
            await player.set_filter(eq, fast_apply=True)
        await interaction.response.defer()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return False
        else:
            return True

    async def on_timeout(self):
        await self.ctx.send("Timed out!")


playlistURLs = {
    dsettings.playlist_1_name: dsettings.playlist_1_url,
    dsettings.playlist_2_name: dsettings.playlist_2_url,
    dsettings.playlist_3_name: dsettings.playlist_3_url,
    dsettings.playlist_4_name: dsettings.playlist_4_url,
    dsettings.playlist_5_name: dsettings.playlist_5_url,
    dsettings.playlist_6_name: dsettings.playlist_6_url,
    dsettings.playlist_7_name: dsettings.playlist_7_url,
    dsettings.playlist_8_name: dsettings.playlist_8_url
}


class playlistSelector(discord.ui.Select):
    def __init__(self, music, ctx):
        self.music = music
        self.ctx = ctx
        options = [
            discord.SelectOption(label=dsettings.select_playlist, default=True),
            discord.SelectOption(label=dsettings.playlist_1_name),
            discord.SelectOption(label=dsettings.playlist_2_name),
            discord.SelectOption(label=dsettings.playlist_3_name),
            discord.SelectOption(label=dsettings.playlist_4_name),
            discord.SelectOption(label=dsettings.playlist_5_name),
            discord.SelectOption(label=dsettings.playlist_6_name),
            discord.SelectOption(label=dsettings.playlist_7_name),
            discord.SelectOption(label=dsettings.playlist_8_name),
        ]
        super().__init__(placeholder="Select Playlist", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await self.ctx.invoke(self.music.play, query=playlistURLs[self.values[0]])
        await interaction.response.defer()


class playlistPlayer(discord.ui.View):
    def __init__(self, *, timeout=120, music, ctx: discord.ext.commands.Context):
        super().__init__(timeout=timeout)
        self.add_item(playlistSelector(music=music, ctx=ctx))
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return False
        else:
            return True


class songButton(discord.ui.Button):
    def __init__(self, number):
        super().__init__(style=discord.ButtonStyle.success, label=number)
        self.interaction = None
        self.number = int(number)
        self.interacted = False

    async def callback(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.interacted = True
        await interaction.response.defer()


class addSong(discord.ui.View):
    def __init__(self, *, timeout=120, ctx):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.buttona = songButton("1")
        self.buttonb = songButton("2")
        self.buttonc = songButton("3")
        self.buttond = songButton("4")
        self.buttone = songButton("5")
        self.add_item(self.buttona)
        self.add_item(self.buttonb)
        self.add_item(self.buttonc)
        self.add_item(self.buttond)
        self.add_item(self.buttone)
        self.buttons = [self.buttona, self.buttonb, self.buttonc, self.buttond, self.buttone]

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return False
        else:
            return True


class topTrackDropdown(discord.ui.Select):
    def __init__(self, songs, ctx, music):
        self.songs = songs
        self.ctx = ctx
        self.music = music
        options = [
            discord.SelectOption(label=dsettings.select_track, default=True),
        ]
        for song in songs:
            options.append(discord.SelectOption(label=song[0], value=song[1]))
        super().__init__(placeholder="Select Track", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await self.ctx.invoke(self.music.play, query=self.values[0])
        await interaction.response.defer()


class topTrackSelector(discord.ui.View):
    def __init__(self, *, timeout=120, songs, ctx: discord.ext.commands.Context, music):
        super().__init__(timeout=timeout)
        self.add_item(topTrackDropdown(songs=songs, ctx=ctx, music=music))
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return False
        else:
            return True
