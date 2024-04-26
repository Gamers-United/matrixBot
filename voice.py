#  Copyright 2023 Macauley Lim xmachd@gmail.com. Based upon the VoiceMaster discord bots open source version:
#  https://github.com/SamSanai/VoiceMaster-Discord-Bot/tree/master
#  This code is licensed under GNU AFFERO GENERAL PUBLIC LICENSE v3.0.
#  A copy of this license should have been provided with the code download, if not see https://www.gnu.org/licenses/
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU AGPL v3.0 for more details.

import asyncio
import logging
import sqlite3

import discord
from discord.ext import commands

from config import settings as dsettings


class voice(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.ext.commands.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, _, after):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        guild_id = member.guild.id
        c.execute("SELECT channel_id FROM guilds WHERE guild_id = ?", (guild_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            pass
        else:
            voice_channel_id = voice_channel[0]
            try:
                if after.channel.id == voice_channel_id:
                    c.execute("SELECT * FROM voice_channels WHERE user_id = ?", (member.id,))
                    cooldown = c.fetchone()
                    if cooldown is None:
                        pass
                    else:
                        await self.bot.channels["VOICE"].send(
                            f"{member.mention} You've been put on a 10 second cooldown!")
                        await asyncio.sleep(10)
                    c.execute("SELECT category_id FROM guilds WHERE guild_id = ?", (guild_id,))
                    voice_channel = c.fetchone()
                    c.execute("SELECT channel_name, channel_limit FROM user_settings WHERE userID = ?", (member.id,))
                    setting = c.fetchone()
                    c.execute("SELECT channel_limit FROM guild_settings WHERE guildID = ?", (guild_id,))
                    guild_settings = c.fetchone()
                    if setting is None:
                        name = f"{member.name}'s channel"
                        if guild_settings is None:
                            limit = 0
                        else:
                            limit = guild_settings[0]
                    else:
                        if guild_settings is None:
                            name = setting[0]
                            limit = setting[1]
                        elif guild_settings is not None and setting[1] == 0:
                            name = setting[0]
                            limit = guild_settings[0]
                        else:
                            name = setting[0]
                            limit = setting[1]
                    category_id = voice_channel[0]
                    member_id = member.id
                    category = self.bot.get_channel(category_id)
                    new_channel = await member.guild.create_voice_channel(name, category=category)
                    new_chanel_id = new_channel.id
                    await member.move_to(new_channel)
                    await new_channel.set_permissions(self.bot.user, connect=True, read_messages=True)
                    await new_channel.edit(name=name, user_limit=limit)
                    c.execute("INSERT INTO voice_channels VALUES (?, ?)", (member_id, new_chanel_id))
                    conn.commit()

                    def check(_x, _y, _z):
                        return len(new_channel.members) == 0

                    await self.bot.wait_for('voice_state_update', check=check)
                    await new_channel.delete()
                    await asyncio.sleep(3)
                    c.execute('DELETE FROM voice_channels WHERE user_id=?', (member_id,))
            except Exception as e:
                logging.error(f"An exception occurred handling voice state update change:\n{e}")
                pass
        conn.commit()
        conn.close()

    @commands.group()
    async def voice(self, ctx):
        pass

    @voice.command()
    async def setup(self, ctx, channel_id, category_id):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        guild_id = ctx.guild.id
        author_id = ctx.author.id
        c.execute("SELECT * FROM guilds WHERE guild_id = ? AND ownerID=?", (guild_id, author_id))
        voice_channel = c.fetchone()
        if voice_channel is None:
            c.execute("INSERT INTO guilds VALUES (?, ?, ?, ?)", (guild_id, author_id, channel_id, category_id))
        else:
            c.execute(
                "UPDATE guilds SET guild_id = ?, owner_id = ?, channel_id = ?, category_id = ? WHERE guild_id = ?",
                (guild_id, author_id, channel_id, category_id, guild_id))
        await ctx.channel.send("**You are all setup and ready to go!**")
        conn.commit()
        conn.close()

    @commands.command()
    async def setlimit(self, ctx, num):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        if ctx.author.id == ctx.guild.owner.id:
            c.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (ctx.guild.id,))
            voice_channel = c.fetchone()
            if voice_channel is None:
                c.execute("INSERT INTO guild_settings VALUES (?, ?, ?)",
                          (ctx.guild.id, f"{ctx.author.name}'s channel", num))
            else:
                c.execute("UPDATE guild_settings SET channel_limit = ? WHERE guild_id = ?", (num, ctx.guild.id))
            await ctx.send("You have changed the default channel limit for your server!")
        else:
            await ctx.channel.send(f"{ctx.author.mention} only the owner of the server can setup the bot!")
        conn.commit()
        conn.close()

    @setup.error
    async def info_error(self, _, error):
        logging.error(error)

    @voice.command()
    async def lock(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_id = ctx.author.id
        c.execute("SELECT voice_id FROM voice_channels WHERE user_id = ?", (author_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            voice_channel_id = voice_channel[0]
            role = ctx.guild.default_role
            channel = self.bot.get_channel(voice_channel_id)
            await channel.set_permissions(role, connect=False)
            await ctx.channel.send(f'{ctx.author.mention} Voice chat locked! 🔒')
        conn.commit()
        conn.close()

    @voice.command()
    async def unlock(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_id = ctx.author.id
        c.execute("SELECT voice_id FROM voice_channels WHERE user_id = ?", (author_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channel_id = voice_channel[0]
            role = ctx.guild.default_role
            channel = self.bot.get_channel(channel_id)
            await channel.set_permissions(role, connect=True)
            await ctx.channel.send(f'{ctx.author.mention} Voice chat unlocked! 🔓')
        conn.commit()
        conn.close()

    @voice.command(aliases=["allow"])
    async def permit(self, ctx, member: discord.Member):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_id = ctx.author.id
        c.execute("SELECT voice_id FROM voice_channels WHERE user_id = ?", (author_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channel_id = voice_channel[0]
            channel = self.bot.get_channel(channel_id)
            await channel.set_permissions(member, connect=True)
            await ctx.channel.send(
                f'{ctx.author.mention} You have permitted {member.name} to have access to the channel. ✅')
        conn.commit()
        conn.close()

    @voice.command(aliases=["deny"])
    async def reject(self, ctx, member: discord.Member):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        c.execute("SELECT voice_id FROM voice_channels WHERE user_id = ?", (author_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channel_id = voice_channel[0]
            channel = self.bot.get_channel(channel_id)
            for members in channel.members:
                if members.id == member.id:
                    c.execute("SELECT channel_id FROM guilds WHERE guild_id = ?", (guild_id,))
                    voice_channel = c.fetchone()
                    channel2 = self.bot.get_channel(voice_channel[0])
                    await member.move_to(channel2)
            await channel.set_permissions(member, connect=False, read_messages=True)
            await ctx.channel.send(
                f'{ctx.author.mention} You have rejected {member.name} from accessing the channel. ❌')
        conn.commit()
        conn.close()

    @voice.command()
    async def limit(self, ctx, limit):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_id = ctx.author.id
        c.execute("SELECT voice_id FROM voice_channels WHERE user_id = ?", (author_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channel_id = voice_channel[0]
            channel = self.bot.get_channel(channel_id)
            await channel.edit(user_limit=limit)
            await ctx.channel.send(f'{ctx.author.mention} You have set the channel limit to be ' + '{}!'.format(limit))
            c.execute("SELECT channel_name FROM user_settings WHERE user_id = ?", (author_id,))
            voice_channel = c.fetchone()
            if voice_channel is None:
                c.execute("INSERT INTO user_settings VALUES (?, ?, ?)", (author_id, f'{ctx.author.name}', limit))
            else:
                c.execute("UPDATE user_settings SET channel_limit = ? WHERE user_id = ?", (limit, author_id))
        conn.commit()
        conn.close()

    @voice.command()
    async def name(self, ctx, *, name):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_id = ctx.author.id
        c.execute("SELECT voice_id FROM voice_channels WHERE user_id = ?", (author_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            voice_channel_id = voice_channel[0]
            channel = self.bot.get_channel(voice_channel_id)
            await channel.edit(name=name)
            await ctx.channel.send(f'{ctx.author.mention} You have changed the channel name to ' + '{}!'.format(name))
            c.execute("SELECT channel_name FROM user_settings WHERE user_id = ?", (author_id,))
            voice_channel = c.fetchone()
            if voice_channel is None:
                c.execute("INSERT INTO user_settings VALUES (?, ?, ?)", (author_id, name, 0))
            else:
                c.execute("UPDATE user_settings SET channel_name = ? WHERE user_id = ?", (name, author_id))
        conn.commit()
        conn.close()

    @voice.command()
    async def claim(self, ctx):
        x = False
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_channel = ctx.author.voice.channel
        if author_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} you're not in a voice channel.")
        else:
            author_id = ctx.author.id
            c.execute("SELECT user_id FROM voice_channels WHERE voice_id = ?", (author_channel.id,))
            voice_channel = c.fetchone()
            if voice_channel is None:
                await ctx.channel.send(f"{ctx.author.mention} You can't own that channel!")
            else:
                for data in author_channel.members:
                    if data.id == voice_channel[0]:
                        owner = ctx.guild.get_member(voice_channel[0])
                        await ctx.channel.send(
                            f"{ctx.author.mention} This channel is already owned by {owner.mention}!")
                        x = True
                if x is False:
                    await ctx.channel.send(f"{ctx.author.mention} You are now the owner of the channel!")
                    c.execute("UPDATE voice_channels SET user_id = ? WHERE voice_id = ?",
                              (author_id, author_channel.id))
            conn.commit()
            conn.close()

    @voice.command()
    async def ghost(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_id = ctx.author.id
        c.execute("SELECT voice_id FROM voice_channels WHERE user_id = ?", (author_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channel_id = voice_channel[0]
            voice_channel = self.bot.get_channel(channel_id)
            cv = discord.PermissionOverwrite(view_channel=False, speak=False, connect=False)
            await voice_channel.set_permissions(ctx.author.guild.default_role, overwrite=cv)
            await ctx.channel.send(f'{ctx.author.mention} You have changed the channel visibility to hidden.')
        conn.commit()
        conn.close()

    @voice.command()
    async def unghost(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        author_id = ctx.author.id
        c.execute("SELECT voice_id FROM voice_channels WHERE user_id = ?", (author_id,))
        voice_channel = c.fetchone()
        if voice_channel is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channel_id = voice_channel[0]
            channel = self.bot.get_channel(channel_id)
            cv = discord.PermissionOverwrite(view_channel=None, speak=None, connect=None)
            await channel.set_permissions(ctx.author.guild.default_role, overwrite=cv)
            await ctx.channel.send(f'{ctx.author.mention} You have changed the channel visibility to visible.')
        conn.commit()
        conn.close()

    @voice.command()
    async def muteAll(self, ctx):
        if ctx.guild.id == dsettings.guild_secondary:
            if ctx.author.voice and ctx.author.voice.channel:
                if ctx.channel.permissions_for(ctx.author.voice.channel).mute_members:
                    for member in ctx.author.voice.channel.members:
                        await member.edit(mute=True)

    @voice.command()
    async def unMuteAll(self, ctx):
        if ctx.guild.id == dsettings.guild_secondary:
            if ctx.author.voice and ctx.author.voice.channel:
                if ctx.channel.permissions_for(ctx.author.voice.channel).mute_members:
                    for member in ctx.author.voice.channel.members:
                        await member.edit(mute=False)


async def setup(bot):
    await bot.add_cog(voice(bot))
