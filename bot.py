import os, json, sys
import discord
from discord.ext import commands
from types import SimpleNamespace
from datetime import datetime
import asyncio

#Bot Static
prefix = "!"
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None, case_insensitive=True)
log = {}
with open("settings.json", "r+") as settingsfile:
    config = json.load(settingsfile)
    token = config["TOKEN"]
    guildids = {
        "MAIN": config["MAIN_GUILD"],
        "PPD": config["SECONDARY_GUILD"]
    }
    echo = config["DEBUG"]
    channelids = {
        "VLOG": config["CHANNELID_VOICELOG"],
        "ILOG": config["CHANNELID_INFRACTIONLOG"],
        "ELOG": config["CHANNELID_ERRORLOG"]
    }

#main bot definitions
@bot.event
async def on_ready():
    bot.appInfo = await bot.application_info()
    print("Bot's name is "+str(bot.user))
    try:
        guild = discord.utils.get(bot.guilds, id=int(guildids["MAIN"]))
        print("Found main guild of ID: "+str(guild.id)+" | Name of: "+str(guild.name))
        print("Members online: "+str(guild.member_count))
    except AttributeError:
        print("Could not find main guild!")
    try:
        guild = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
        print("Found HQ discord guild of ID: "+str(guild.id)+" | Name of: "+str(guild.name))
        print("Members online: "+str(guild.member_count))
    except AttributeError:
        print("Could not find HQ guild!")
    try:
        log["VOICE"] = bot.get_channel(int(channelids["VLOG"]))
        log["INFRACTIONS"] = bot.get_channel(int(channelids["VLOG"]))
        log["ERROR"] = bot.get_channel(int(channelids["ELOG"]))
    except:
        print("Error finding channels")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found!")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing a required argument. Do "+str(prefix)+"help")
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the required permissions to run this command.")
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("MLtech Matrix is missing required permissions. Please contact an Admin")
    else:
        print(error)

#bot logging
@bot.event
async def on_voice_state_update(member, before, after):
    timenow = datetime.now()
    embed=discord.Embed(title="New Voice State", description=str(member.name)+" "+str(timenow))
    embed.add_field(name="AFK", value=after.afk, inline=False)
    try:
        embed.add_field(name="Channel", value=str(after.channel.id)+"\n"+after.channel.category.name+" | "+after.channel.guild.name+" | "+after.channel.name, inline=False)
    except AttributeError:
        embed.add_field(name="Channel", value="N/A", inline=False)
    embed.add_field(name="Deafened", value=after.deaf, inline=False)
    embed.add_field(name="Muted", value=after.mute, inline=False)
    embed.add_field(name="Requested To Speak Timestamp", value=after.requested_to_speak_at, inline=False)
    embed.add_field(name="Self Deafened", value=after.self_deaf, inline=False)
    embed.add_field(name="Self Muted", value=after.self_mute, inline=False)
    embed.add_field(name="Streaming", value=after.self_stream, inline=False)
    embed.add_field(name="Video", value=after.self_video, inline=False)
    embed.add_field(name="Supressed", value=after.suppress, inline=False)
    await log["VOICE"].send(embed=embed)

#help command
@bot.command()
async def help(ctx):
    embed=discord.Embed(title="Matrix Help", description="""These are all the commands available, with Matrix.""", color=0x00ff00)
    embed.add_field(name="Music | Basic", value="""play 'link or name'
    pause
    resume
    nowplaying (np)
    seek
    queue
    remove
    skip""", inline=False)
    embed.add_field(name="Music | Advanced", value="""volume 'level'
    eq 'band 0-14' 'level -0.25 to 1.0'
    reseteq""", inline=False)
    embed.add_field(name="Fun | Jokes", value="""joke
    dadjoke
    copypasta""", inline=False)
    embed.add_field(name="Fun | Random", value="""roll '3d6' (Syntax: https://d20.readthedocs.io/en/latest/start.html#dice-syntax)
    reorder '1,2,3,4' (Comma Seperated List)
    pick '1,2,3,4' (Comma Seperated List)""", inline=False)
    embed.add_field(name="Voice | User", value="""voice lock
    voice unlock
    voice permit 'member'
    voice reject 'member'
    voice limit 'number'
    voice name 'name'
    voice claim
    voice ghost
    voice unghost""", inline=False)
    embed.add_field(name="Voice | Admin", value="""voice setup 'channel id' 'category id'
    voice setlimit 'number'""", inline=False)
    embed.add_field(name="Development", value="""shutdown
    reload""", inline=False)
    await ctx.send(embed=embed)

#run the bot
async def main():
    async with bot:
        await bot.start(token)
        await bot.load_extension('cogs.randomresults')
        await bot.load_extension('cogs.voice')
        await bot.load_extension('cogs.dev')
        await bot.load_extension('cogs.music')
        await bot.load_extension('cogs.humor')

asyncio.run(main())