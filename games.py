#  Copyright 2023 Macauley Lim xmachd@gmail.com
#  This code is licensed under GNU AFFERO GENERAL PUBLIC LICENSE v3.0.
#  A copy of this license should have been provided with the code download, if not see https://www.gnu.org/licenses/
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU AGPL v3.0 for more details.

import multiprocessing
import os
import re
import sys
import uuid

import aiohttp.web_request
import discord
from aiohttp import web
from discord.ext import commands


def solveCraftablesProblem(items: [], queue: multiprocessing.Queue):  # [(name: str, qty: float)]
    v2_loc = os.getcwd() + "/calculator/v2"
    sys.path.insert(0, v2_loc)
    from calculator import v2
    solver = v2.solver.Solver()
    for item in items:
        name = item[0]
        qty = item[1]
        solver.addSolvable(v2.globalvar.gameIngredients[name].getQty(qty))
    solver.solve()
    aid = str(uuid.uuid4())
    solver.writeSankey(os.getcwd() + "/sankey/" + aid + ".html")
    queue.put(aid)
    final_resources = str(solver.ingredientTiersHolder[solver.currentTier])
    queue.put(final_resources)
    queue.put(solver.craftablePrintHolder)
    queue.put(solver.currentTier)


def webServer():
    async def handler(request: aiohttp.web_request.Request):
        url = str(request.rel_url)
        if "matrix.mltech.au:6000" not in str(request.host):
            return web.Response(body=f"Invalid Host: {request.host}")
        try:
            auuid = re.search("\/sankey\/(.+)", url).group(1)
            with open(os.getcwd() + "/sankey/" + auuid, mode='r') as f:
                return web.Response(body=str(f.read()), content_type='text/html')
        except AttributeError:
            return web.Response(body="Error: No Content.")

    # logging.basicConfig(level=logging.DEBUG)
    app = web.Application()
    app.router.add_get("/", handler)
    app.router.add_get("/sankey/{id}", handler)
    web.run_app(app, port=6000)


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.system("cd sankey && rm *")

    @commands.command()
    async def solve(self, ctx, *, items: str):
        queue = multiprocessing.Queue()
        craftables = items.split(" ")
        output = []
        b = None
        for item in craftables:
            a = item.split(":")
            if len(a) > 2:
                b = f"{a[0]}:{a[1]}"
                qty = float(a[2])
            else:
                b = f"{a[0]}:{a[1]}"
                qty = 1.0
            output.append((b, qty))
        p = multiprocessing.Process(target=solveCraftablesProblem, args=(output, queue))
        p.start()
        htmlid = queue.get()
        final_resources = queue.get()
        cph = queue.get()
        ct = queue.get()
        craftables_string = ",".join(craftables)
        embed = discord.Embed(title=f"**Crafting Steps For:** {craftables_string}",
                              url=f"http://matrix.mltech.au:6000/sankey/{htmlid}.html")
        await ctx.send(embed=embed)
        for i in range(0, ct):
            await ctx.send(f"**Tier {i} Crafts:**\n{cph[i]}")
        await ctx.send(f"**Total Resources:**\n{final_resources}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GameCommands(bot))
