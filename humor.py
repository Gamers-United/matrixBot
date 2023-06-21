#  Copyright 2023 Macauley Lim xmachd@gmail.com
#  This code is licensed under GNU AFFERO GENERAL PUBLIC LICENSE v3.0.
#  A copy of this license should have been provided with the code download, if not see https://www.gnu.org/licenses/
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU AGPL v3.0 for more details.

import random

from discord.ext import commands


class Humor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def joke(self, ctx):
        """Provides a regular joke"""
        lines = open("data/jokes.txt").read().splitlines()
        myline = random.choice(lines)
        await ctx.send(myline)

    @commands.command()
    async def dadjoke(self, ctx):
        """Provide's a dadjoke"""
        lines = open("data/dadjokes.txt").read().splitlines()
        myline = random.choice(lines)
        await ctx.send(myline)

    @commands.command()
    async def copypasta(self, ctx):
        """Provide's a copypasta"""
        lines = open("data/copypasta.txt").read().splitlines()
        myline = random.choice(lines)
        await ctx.send(myline)


async def setup(bot):
    await bot.add_cog(Humor(bot))
