import discord, random
from discord.ext import commands

class Humor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def joke(self, ctx):
        """Provides a regular joke"""
        lines = open("jokes.txt").read().splitlines()
        myline = random.choice(lines)
        await ctx.send(myline)

    @commands.command()
    async def dadjoke(self, ctx):
        """Provide's a dadjoke"""
        lines = open("dadjokes.txt").read().splitlines()
        myline = random.choice(lines)
        await ctx.send(myline)

    @commands.command()
    async def copypasta(self, ctx):
        """Provide's a copypasta"""
        lines = open("copypasta.txt").read().splitlines()
        myline = random.choice(lines)
        await ctx.send(myline)

def setup(bot):
    bot.add_cog(Humor(bot))