import discord, d20, random
from discord.ext import commands

class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def roll(self, ctx, request:str):
        embed = discord.Embed(title="Roll Result", description="Need help with the syntax? View the docs: https://d20.readthedocs.io/en/latest/start.html#dice-syntax")
        roll = d20.roll(request)
        embed.add_field("Results", str(roll))
        await ctx.send(embed=embed)
    @commands.command()
    async def reorder(self, ctx, request:str):
        values = request.split(',')
        random.shuffle(values)
        embed = discord.Embed(title="Reordered Result", description=str(values))
        await ctx.send(embed=embed)
    @commands.command()
    async def pick(self, ctx, request:str):
        values = request.split(',')
        values = random.choice(values)
        embed = discord.Embed(title="Picked Result", description=str(values))
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Random(bot))