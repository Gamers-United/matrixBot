import discord
from discord.ext import commands

class DevCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shutdown(self, ctx):
        if ctx.author.guild_permissions.administrator == True:
            await ctx.send("Bot shutting down!")
            await self.bot.close()
        else:
            await ctx.send("Don't shut down the bot, you filthy animal!")

    @commands.command()
    async def reload(self, ctx):
        if ctx.author.guild_permissions.administrator == True:
            await ctx.send("Bot reloading!")
            await self.bot.unload_extension('voice')
            await self.bot.load_extension('voice')
            await self.bot.unload_extension('randomresults')
            await self.bot.load_extension('randomresults')
            await self.bot.unload_extension('music')
            await self.bot.load_extension('music')
            await self.bot.unload_extension('humor')
            await self.bot.load_extension('humor')
        else:
            await ctx.send("Don't shut down the bot, you filthy animal!")

async def setup(bot):
    await bot.add_cog(DevCommands(bot))