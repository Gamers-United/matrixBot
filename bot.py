import os, json, sys
import discord
from discord.ext import commands
from types import SimpleNamespace
from datetime import datetime
import asyncio
from config import settings as dsettings
import traceback

#Bot Static
prefix = "!"
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None, case_insensitive=True)
bot.channels = {}

#main bot definitions
@bot.event
async def on_ready():
    #only load modules that are in config
    if dsettings.jokes:
        await bot.load_extension('randomresults')
        await bot.load_extension('humor')
    if dsettings.voice:
        await bot.load_extension('voice')
    if dsettings.music:
        await bot.load_extension('music')
    if dsettings.development:
        await bot.load_extension('dev')
    
    #hold the details of the application info inside the bot object
    bot.appInfo = await bot.application_info()
    print("Bot's name is "+str(bot.user))
    
    #startup info print
    try:
        guild = discord.utils.get(bot.guilds, id=int(dsettings.guild_main))
        print(f"Found main guild of ID: {str(guild.id)} | Name of: {str(guild.name)}")
        print(f"Members online: {str(guild.member_count)}")
    except AttributeError:
        print("Could not find main guild!")
    try:
        guild = discord.utils.get(bot.guilds, id=int(dsettings.guild_secondary))
        print(f"Found HQ discord guild of ID: {str(guild.id)} | Name of: {str(guild.name)}")
        print(f"Members online: {str(guild.member_count)}")
    except AttributeError:
        print("Could not find HQ guild!")

    #save these channels for later use
    try:
        bot.channels["VOICE"] = bot.get_channel(int(dsettings.channelid_voice_log))
        bot.channels["INFRACTIONS"] = bot.get_channel(int(dsettings.channelid_infraction_log))
        bot.channels["ERROR"] = bot.get_channel(int(dsettings.channelid_error_log))
    except:
        print("Error finding channels")

#bot command error
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found!")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing a required argument. Do {str(prefix)}help")
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the required permissions to run this command.")
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("MLtech Matrix is missing required permissions. Please contact an Admin")
    if isinstance(error, commands.CommandInvokeError):
        print(f"{error}.\n Traceback:")
        print(''.join(traceback.format_tb(error.e.__traceback__)))
    else:
        print(error)

#bot logging
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    timenow = datetime.now()
    embed=discord.Embed(title=f"{member.name}", description=str(member.name)+" "+str(timenow))
    if not before.channel and after.channel is not None:
        embed.add_field(name="Joined", value=f"{after.channel.name}/{after.channel.category.name}/{after.channel.guild.name}")
    elif before.channel is not None and not after.channel:
        embed.add_field(name="Left", value=f"{before.channel.name}/{before.channel.category.name}/{before.channel.guild.name}")
    elif after.afk and before.channel is not None:
        embed.add_field(name="Went AFK", value=f"{before.channel.guild.name}")
    elif not before.self_deaf and after.self_deaf:
        embed.add_field(name="Deafened Themselves", value=f"{before.channel.guild.name}")
    elif before.self_deaf and not after.self_deaf:
        embed.add_field(name="Undeafened Themselves", value=f"{before.channel.guild.name}")
    elif not before.self_mute and after.self_mute:
        embed.add_field(name="Muted Themselves", value=f"{before.channel.guild.name}")
    elif before.self_mute and not after.self_mute:
        embed.add_field(name="Unmuted Themselves", value=f"{before.channel.guild.name}")
    elif not before.self_video and after.self_video:
        embed.add_field(name="Has Begun Streaming Video", value=f"{before.channel.guild.name}")
    elif before.self_video and not after.self_video:
        embed.add_field(name="Has Ended Their Video Streaming", value=f"{before.channel.guild.name}")
    elif not before.mute and after.mute:
        embed.add_field(name="Was Muted By An Admin", value=f"{before.channel.guild.name}")
    elif before.mute and not after.mute:
        embed.add_field(name="Was Unmuted by an Admin", value=f"{before.channel.guild.name}")
    elif not before.deaf and after.deaf:
        embed.add_field(name="Was Deafened By An Admin", value=f"{before.channel.guild.name}")
    elif before.deaf and not after.deaf:
        embed.add_field(name="Was Undeafened By An Admin", value=f"{before.channel.guild.name}")
    await bot.channels["VOICE"].send(embed=embed)

#help command
@bot.command()
async def help(ctx):
    embed=discord.Embed(title="Matrix Help", description="""These are all the commands available, with Matrix.""", color=0x00ff00)
    embed.add_field(name="Music | Basic", value="""play 'spotify link, youtube (music) link, sound cloud link, mp3 link or name'
    connect 'channel'
    disconnect, stop, leave, dc
    pause
    resume
    nowplaying, np 
    seek 'time' (Minutes and/or seconds)
    shuffle (current queue)
    repeat (toggle)
    queue 'page'
    lyrics (for the current song)
    remove 'number in queue to remove'
    skip 'number to skip (default of 1)'
    suggested""", inline=False)
    embed.add_field(name="Music | Advanced", value="""volume 'level' (0 to 500%)
    filter (GUI Command)
    delfilter (GUI Command)""", inline=False)
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
        await bot.start(dsettings.token)

if __name__ == "__main__":
    asyncio.run(main())