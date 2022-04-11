import discord
from discord.ext import commands
from musicplayer import CustomPlayer
import lavapy

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
    "Equalizer": [["Band Options", equalizerBandOptions],["Band Gain", equalizerBandGains], ["N/A", noOptions], ["N/A", noOptions]],
}

class filterButtons(discord.ui.View):
    def __init__(self, *, timeout=120, ctx: discord.ext.commands.Context):
        super().__init__(timeout=timeout)
        self.ctx = ctx
    
    @discord.ui.select(placeholder="Select Filter", options=filterOptions)
    async def eqButton(self,select:discord.ui.select,interaction:discord.Interaction):
        await self.ctx.send(view=filterButtonsOptions(self.ctx, filterArgumentOptions[select.value], select.value))

        
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
    async def eqButton(self,select:discord.ui.select,interaction:discord.Interaction):
        player: CustomPlayer = self.ctx.voice_client
        eq = lavapy.Equalizer.flat()
        eq.name = "Equalizer"
        await player.removeFilter(eq)

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
        self.selectora = discord.ui.select(placeholder=self.viewa, options=self.opta) (self.selectorA)
        self.selectorb = discord.ui.select(placeholder=self.viewb, options=self.optb) (self.selectorB)
        self.selectorc = discord.ui.select(placeholder=self.viewc, options=self.optc) (self.selectorC)
        self.selectord = discord.ui.select(placeholder=self.viewd, options=self.optd) (self.selectorD)

    async def selectorA(self,select:discord.ui.select,interaction:discord.Interaction):
        self.valuea = select.value
        
    async def selectorB(self,select:discord.ui.select,interaction:discord.Interaction):
        self.valueb = select.value

    async def selectorC(self,select:discord.ui.select,interaction:discord.Interaction):
        self.valuec = select.value

    async def selectorD(self,select:discord.ui.select,interaction:discord.Interaction):
        self.valued = select.value

    @discord.ui.button()
    async def submitButton(self,button:discord.ui.button,interaction:discord.Interaction):
        player: CustomPlayer = self.ctx.voice_client
        if self.type == "Equalizer":
            if player.filters["Equalizer"] is None:
                eq = lavapy.Equalizer.flat()
                eq.equalizerName = "Equalizer"
            else:
                eq = player.filters["Equalizer"]
            eq.levels[int(self.valuea)] = float(self.valueb)
            await player.addFilter(eq)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return False
        else:
            return True

    async def on_timeout(self):
        await self.ctx.send("Timed out!")
