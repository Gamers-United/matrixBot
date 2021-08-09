import mysql.connector
import os, json
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext

class DiscordHelper(discord.Client):
    def configureConfig(self):
        with open("settings.json", "r+") as settingsfile:
            self.settings = settingsfile
            self.config = json.load(settingsfile)
            self.token = self.config["TOKEN"]
            self.guild = {
                "MAIN": self.config["MAIN_GUILD"],
                "PPD": self.config["SECONDARY_GUILD"]
            }

    async def on_ready(self):
            try:
                guild = discord.utils.get(self.guilds, id=int(self.guild["MAIN"]))
                print("Found main guild of ID: "+str(guild.id)+" | Name of: "+str(guild.name))
                print("Members online: "+str(guild.member_count))
            except AttributeError:
                print("Could not find main guild!")
            try:
                guild = discord.utils.get(self.guilds, id=int(self.guild["PPD"]))
                print("Found private plus project discord guild of ID: "+str(guild.id)+" | Name of: "+str(guild.name))
                print("Members online: "+str(guild.member_count))
            except AttributeError:
                print("Could not find private plus project guild!")
            print("Bot's name is "+str(self.user))

#setup the bot
try:
    matrix = DiscordHelper()
    matrix.configureConfig()
    matrix.run(matrix.token)
except KeyboardInterrupt:
    print("Ending")
    matrix.logout()