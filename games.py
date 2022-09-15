from discord.ext import commands
from config import settings as dsettings
from calculator import v2
import os, uuid


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.solver = None
        self.bot = bot

    @commands.command()
    async def solve(self, ctx, *, items: str):
        self.solver = v2.solver.Solver()
        craftables = items.split(" ")
        b = None
        for item in craftables:
            a = item.split(":")
            if len(a) > 2:
                b = f"{a[0]}:{a[1]}"
                qty = float(a[2])
            else:
                b += f"{a[0]}:{a[1]}"
                qty = 1.0
            self.solver.addSolvable(v2.globalvar.gameIngredients[b].getQty(qty))
        self.solver.solve()
        self.solver.generateFigure()
        identifier = uuid.uuid4()
        try:
            os.mkdir(os.getcwd() + "/sankey")
        except FileExistsError:
            pass
        self.solver.writeSankey(os.getcwd() + "/sankey/" + str(identifier) + ".html")
        await ctx.send("https://matrix.mltech.au:2003/" + str(identifier) + ".html")
