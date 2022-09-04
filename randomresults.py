import d20
import discord
import random
from discord.ext import commands

from config import settings as dsettings

class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, request: str):
        roll = d20.roll(request)
        embed = discord.Embed(title=dsettings.roll_result, description=str(roll))
        embed.add_field(name="Need Help?",
                        value="View the docs: https://d20.readthedocs.io/en/latest/start.html#dice-syntax")
        await ctx.send(embed=embed)

    @commands.command()
    async def reorder(self, ctx, request: str):
        values = request.strip().split(',')
        random.shuffle(values)
        embed = discord.Embed(title=dsettings.reorder_result, description=str(values))
        await ctx.send(embed=embed)

    @commands.command()
    async def pick(self, ctx, request: str):
        values = request.strip().split(',')
        values = random.choice(values)
        embed = discord.Embed(title=dsettings.pick_result, description=str(values))
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Random(bot))
