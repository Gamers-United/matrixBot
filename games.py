from discord.ext import commands
from config import settings as dsettings
from calculator import v2

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
        await ctx.send(self.solver.printResult())
        sankey = self.solver.generateSankey()
        self.solver = v2.solver.Solver()
