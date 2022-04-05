import discord, d20, random
from discord.ext import commands

class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        await ctx.send("An error has occured!\n"+str(error))

    @commands.command()
    async def roll(self, ctx, request:str):
        roll = d20.roll(request)
        embed = discord.Embed(title="Roll Result", description=str(roll))
        embed.add_field(name="Need Help?", value="View the docs: https://d20.readthedocs.io/en/latest/start.html#dice-syntax")
        await ctx.send(embed=embed)

    @commands.command()
    async def reorder(self, ctx, request:str):
        values = request.strip().split(',')
        random.shuffle(values)
        embed = discord.Embed(title="Reordered Result", description=str(values))
        await ctx.send(embed=embed)
        
    @commands.command()
    async def pick(self, ctx, request:str):
        values = request.strip().split(',')
        values = random.choice(values)
        embed = discord.Embed(title="Picked Result", description=str(values))
        await ctx.send(embed=embed)

await def setup(bot):
    async bot.add_cog(Random(bot))