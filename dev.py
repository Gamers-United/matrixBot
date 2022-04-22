import discord
from discord.ext import commands
from config import settings as dsettings

class DevCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shutdown(self, ctx):
        if ctx.author.guild_permissions.administrator == True:
            await ctx.send(dsettings.shutdown)
            await self.bot.close()
        else:
            await ctx.send(dsettings.nopermission)

    @commands.command()
    async def reload(self, ctx):
        if ctx.author.guild_permissions.administrator == True:
            await ctx.send(dsettings.reload)
            if dsettings.jokes:
                await bot.unload_extension('randomresults')
                await bot.unload_extension('humor')
                await bot.load_extension('randomresults')
                await bot.load_extension('humor')
            if dsettings.voice:
                await bot.unload_extension('voice')
                await bot.load_extension('voice')
            if dsettings.music:
                await bot.unload_extension('music')
                await bot.load_extension('music')
            if dsettings.development:
                await bot.unload_extension('dev')
                await bot.load_extension('dev')
        else:
            await ctx.send(dsettings.nopermission)

async def setup(bot):
    await bot.add_cog(DevCommands(bot))