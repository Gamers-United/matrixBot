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
            self.bot.unload_extension('voice')
            self.bot.load_extension('voice')
        else:
            await ctx.send("Don't shut down the bot, you filthy animal!")

def setup(bot):
    bot.add_cog(DevCommands(bot))