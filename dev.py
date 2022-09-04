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
                await self.bot.unload_extension('randomresults')
                await self.bot.unload_extension('humor')
                await self.bot.load_extension('randomresults')
                await self.bot.load_extension('humor')
            if dsettings.voice:
                await self.bot.unload_extension('voice')
                await self.bot.load_extension('voice')
            if dsettings.music:
                await self.bot.unload_extension('music')
                await self.bot.load_extension('music')
            if dsettings.development:
                await self.bot.unload_extension('dev')
                await self.bot.load_extension('dev')
        else:
            await ctx.send(dsettings.nopermission)


async def setup(bot):
    await bot.add_cog(DevCommands(bot))
