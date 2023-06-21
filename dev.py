#  Copyright 2023 Macauley Lim xmachd@gmail.com
#  This code is licensed under GNU AFFERO GENERAL PUBLIC LICENSE v3.0.
#  A copy of this license should have been provided with the code download, if not see https://www.gnu.org/licenses/
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU AGPL v3.0 for more details.

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
            if dsettings.games:
                await self.bot.unload_extension('games')
                await self.bot.load_extension('games')
            if dsettings.dj:
                await self.bot.unload_extension('dj')
                await self.bot.load_extension('dj')
        else:
            await ctx.send(dsettings.nopermission)


async def setup(bot):
    await bot.add_cog(DevCommands(bot))
