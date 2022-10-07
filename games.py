import multiprocessing
import os
import re
import uuid
import sys
import discord

import aiohttp.web_request
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
    queue.put((solver.ingredientTiersHolder[solver.currentTier], solver.craftablePrintHolder, solver.currentTier))
    queue.cancel_join_thread()


def webServer():
    async def handler(request: aiohttp.web_request.Request):
        url = str(request.rel_url)
        if "matrix.mltech.au:2003" not in str(request.host):
            return web.Response(body=f"Invalid Host: {request.host}")
        try:
            auuid = re.search("\/sankey\/(.+)", url).group(1)
            with open(os.getcwd() + "/sankey/" + auuid, mode='r') as f:
                return web.Response(body=str(f.read()), content_type='text/html')
        except AttributeError:
            return web.Response(body="Error: No Content.")

    #logging.basicConfig(level=logging.DEBUG)
    app = web.Application()
    app.router.add_get("/", handler)
    app.router.add_get("/sankey/{id}", handler)
    web.run_app(app, port=2003)


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
                b += f"{a[0]}:{a[1]}"
                qty = 1.0
            output.append((b, qty))
        p = multiprocessing.Process(target=solveCraftablesProblem, args=(output, queue))
        p.start()
        p.join()
        htmlid = queue.get()
        data = queue.get() # (solver.ingredientTiersHolder[ct], solver.craftablePrintHolder, solver.currentTier)
        ith = data[0]
        cph = data[2]
        ct = data[3]
        embed = discord.Embed(title=f"Crafting Steps For items: {str(craftables)}", url=f"http://matrix.mltech.au:2003/sankey/{htmlid}.html")
        for i in range(0, ct):
            embed.add_field(name = f"Tier: {i} Crafts", value=cph[i])
        await ctx.send(embed=embed)
        final_resources = ith
        await ctx.send(f"Total Resources: {final_resources}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GameCommands(bot))
