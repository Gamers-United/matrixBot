import os
import re
import uuid
import aiofiles

import aiohttp.web_request
from aiohttp import web
from discord.ext import commands

from calculator import v2


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.site = None
        self.solver = None
        self.bot: commands.Bot = bot

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

    async def webServer(self):
        async def handler(request: aiohttp.web_request.Request):
            url = request.url()
            if "matrix.mltech.au" not in url:
                return web.Response(status=404)
            uuid = re.search(":2003\/(.+)", url).group(1)
            async with aiofiles.open(os.getcwd() + "/sankey/" + uuid, mode='r') as f:
                return web.Response(body=f.read())
        app = web.Application()
        app.router.add_get("/", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, '0.0.0.0', 2003)
        await self.bot.wait_until_ready()
        await self.site.start()


async def setup(bot: commands.Bot):
    await bot.add_cog(GameCommands(bot))
    bot.loop.create_task(GameCommands.webServer())
