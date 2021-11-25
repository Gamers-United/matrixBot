import os, json, sys
import discord
from discord.ext import commands
from sqlalchemy import create_engine, Column, Integer, String, Table, Text, ForeignKey, PickleType
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from types import SimpleNamespace

#static declerations
prefix = "."
Base = declarative_base()
association_table = Table('association', Base.metadata,
    Column('community_id', ForeignKey('communities.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True)
)
admin_association_table = Table('admin_association', Base.metadata,
    Column('community_id', ForeignKey('communities.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True)
)
invitee_association_table = Table('invitee_association', Base.metadata,
    Column('community_id', ForeignKey('communities.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True)
)
with open("settings.json", "r+") as settingsfile:
    settings = settingsfile
    config = json.load(settingsfile)
    token = config["TOKEN"]
    guildids = {
        "MAIN": config["MAIN_GUILD"],
        "PPD": config["SECONDARY_GUILD"]
    }
    echo = config["DEBUG"]
engine = create_engine("sqlite+pysqlite:///db.db", echo=echo, future=True)
Session = sessionmaker(bind=engine)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)

#SQL Alchemy DB Structure
class Community(Base):
    __tablename__ = 'communities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    fullname = Column(String)
    rules = Column(String)
    categoryid = Column(Integer)

    admins = relationship("User", secondary=admin_association_table, back_populates="groups_admin")
    users = relationship("User", secondary=association_table, back_populates="groups")
    invited = relationship("User", secondary=invitee_association_table, back_populates="pendingjoins")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    did = Column(Integer)
    groups = relationship("Community", secondary=association_table, back_populates="users")
    groups_admin = relationship("Community", secondary=admin_association_table, back_populates="admins")
    pendingjoins = relationship("Community", secondary=invitee_association_table, back_populates="invited")

#DB Setup
Base.metadata.create_all(engine)

#Cog definitions
class PPProject(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def newcommunity(self, ctx, shortname):
        if ctx.channel.id == 869510758164201532:
            guild_main = discord.utils.get(bot.guilds, id=int(guildids["MAIN"]))
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            user = db.query(User).filter_by(did=ctx.author.id).first()
            admin_user = user
            if user is None:
                new_user = User(did=ctx.author.id)
                admin_user = new_user
                db.add(new_user)
            community = db.query(Community).filter_by(name=shortname).first()
            if community is None:
                new_community = Community(name=shortname, fullname=shortname, rules="Add rules here")
                new_community.admins = [admin_user]
                arole = discord.utils.get(guild_ppd.roles, id=868375117384806470)
                channel_category = await guild_ppd.create_category(shortname, overwrites={ctx.author: discord.PermissionOverwrite(
                    manage_channels=True, manage_messages=True, move_members=True, mute_members=True, read_messages=True, send_messages=True, view_channel=True, speak=True, connect=True, deafen_members=True
                ), guild_ppd.default_role: discord.PermissionOverwrite(view_channel=False), arole: discord.PermissionOverwrite(connect=True, attach_files=True, add_reactions=True, manage_channels=True, manage_messages=True, manage_permissions=True, mention_everyone=True, move_members=True, mute_members=True, priority_speaker=True, read_messages=True, read_message_history=True, send_messages=True, send_tts_messages=True, speak=True, use_slash_commands=True, view_channel=True)})
                new_community.categoryid = channel_category.id
                db.add(new_community)
                db.commit()
                new_text = await guild_ppd.create_text_channel("general", category=channel_category)
                new_voice = await guild_ppd.create_voice_channel("general", category=channel_category)
                await ctx.send("New community made: "+str(shortname)+", Checkout the B&B Community Discord to make your community!")
            else:
                await ctx.send("Name already in use!")
        else:
            await ctx.send("Please use B&B Communities #bot-spam")

    @commands.command()
    async def hidecommunity(self, ctx, shortname):
        if ctx.author.guild_permissions.administrator == True:
            guild_main = discord.utils.get(bot.guilds, id=int(guildids["MAIN"]))
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            community = db.query(Community).filter_by(name=shortname).first()
            arole = discord.utils.get(guild_ppd.roles, id=868375117384806470)
            category = guild_ppd.get_channel(community.categoryid)
            await category.set_permissions(arole, overwrite=None)
            await ctx.send("Hid community from admin view!")
        else:
            await ctx.send("What are you doing, you filthy animal!")

    @commands.command()
    async def showcommunity(self, ctx, shortname):
        if ctx.author.guild_permissions.administrator == True:
            guild_main = discord.utils.get(bot.guilds, id=int(guildids["MAIN"]))
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            community = db.query(Community).filter_by(name=shortname).first()
            arole = discord.utils.get(guild_ppd.roles, id=868375117384806470)
            category = guild_ppd.get_channel(community.categoryid)
            await category.set_permissions(arole, connect=True, attach_files=True, add_reactions=True, manage_channels=True, manage_messages=True, manage_permissions=True, mention_everyone=True, move_members=True, mute_members=True, priority_speaker=True, read_messages=True, read_message_history=True, send_messages=True, send_tts_messages=True, speak=True, use_slash_commands=True, view_channel=True)
            await ctx.send("Showing community to admin view!")
        else:
            await ctx.send("What are you doing, you filthy animal!")

    @commands.command()
    async def listcommunities(self, ctx):
        if ctx.author.guild_permissions.administrator == True:
            db = Session()
            communities = db.query(Community).all()
            communitystring = ""
            for c in communities:
                communitystring = communitystring + c.name + ", "  
            await ctx.send(communitystring)
        else:
            await ctx.send("What are you doing, you filthy animal!")


    @commands.command()
    async def deletecommunity(self, ctx, shortname):
        if ctx.channel.id == 869510758164201532:
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            user = db.query(User).filter_by(did=ctx.author.id).first()
            community = db.query(Community).filter_by(name=shortname).first()
            if community is None:
                await ctx.send("Community not found! Make sure to use the exact shortname.")
            elif user in community.admins:
                await ctx.send("Deletion started!")
                category = guild_ppd.get_channel(community.categoryid)
                for channel in category.channels:
                    await channel.delete()
                await category.delete()
                db.delete(community)
                db.commit()
                await ctx.send("Deletion finished!")
            elif ctx.author.guild_permissions.administrator:
                await ctx.send("Deletion started!")
                category = guild_ppd.get_channel(community.categoryid)
                for channel in category.channels:
                    await channel.delete()
                await category.delete()
                db.delete(community)
                db.commit()
                await ctx.send("Deletion finished!")
            else:
                await ctx.send("No Permission!")
        else:
            await ctx.send("Please use B&B Communities #bot-spam")

    @commands.command()
    async def invite(self, ctx, com, member: discord.Member):
        guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
        db = Session()
        user = db.query(User).filter_by(did=member.id).first()
        fuser = user
        if user is None:
            new_user = User(did=member.id)
            fuser = new_user
            db.add(new_user)
        invitinguser = db.query(User).filter_by(did=ctx.author.id).first()
        community = db.query(Community).filter_by(name=com).first()
        if invitinguser in community.admins:
            if community is None:
                await ctx.send("Community not found! Make sure to use the exact shortname.")
            else:
                community.invited.append(fuser)
                dm = await member.create_dm()
                await dm.send("You have been invited to the B&B Community: "+str(community.name))
                await dm.send("Type ```.accept "+str(community.name)+"``` in B&Bommunities #bot-spam to accept the invite!")
                await dm.send("https://discord.gg/8MgJ3ChMtt")
                await ctx.send(member.name+" has been invited to "+str(community.name)+"!")
        else:
            await ctx.send("No permission! Contact your Communities admin to add new members.")
        db.commit()

    @commands.command()
    async def accept(self, ctx, com):
        if ctx.channel.id == 869510758164201532:
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            user = db.query(User).filter_by(did=ctx.author.id).first()
            if user is None:
                new_user = User(did=ctx.author.id)
                db.add(new_user)
            community = db.query(Community).filter_by(name=com).first()
            if community is None:
                await ctx.send("Community not found or you have not been invited! Make sure to use the exact shortname.")
            elif user in community.invited:
                community.invited.remove(user)
                community.users.append(user)
                guildmember = await guild_ppd.fetch_member(ctx.author.id)
                cat = discord.utils.get(guild_ppd.categories, id=int(community.categoryid))
                await cat.set_permissions(guildmember, read_messages=True, send_messages=True, view_channel=True, speak=True, connect=True)
                for chan in cat.channels:
                    await chan.set_permissions(guildmember, read_messages=True, send_messages=True, view_channel=True, speak=True, connect=True)
                await ctx.send("Successfully joined community!")
                db.commit()
            else:
                await ctx.send("Community not found or you have not been invited! Make sure to use the exact shortname.")
        else:
            await ctx.send("Please use B&B Communities #bot-spam")

    @commands.command()
    async def leave(self, ctx, com):
        if ctx.channel.id == 869510758164201532:
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            user = db.query(User).filter_by(did=ctx.author.id).first()
            if user is None:
                new_user = User(did=ctx.author.id)
                db.add(new_user)
            community = db.query(Community).filter_by(name=com).first()
            if community is None:
                await ctx.send("Community not found or you are not part of that community! Make sure to use the exact shortname.")
            elif user in community.users:
                community.users.remove(user)
                guildmember = await guild_ppd.fetch_member(ctx.author.id)
                cat = discord.utils.get(guild_ppd.categories, id=int(community.categoryid))
                await cat.set_permissions(guildmember, read_messages=None, send_messages=None, view_channel=None, speak=None, connect=None)
                for chan in cat.channels:
                    await chan.set_permissions(guildmember, read_messages=None, send_messages=None, view_channel=None, speak=None, connect=None)
                await ctx.send("Successfully left community!")
                db.commit()
            else:
                await ctx.send("Community not found or you are not part of that community! Make sure to use the exact shortname.")
        else:
            await ctx.send("Please use B&B Communities #bot-spam")

    @commands.command()
    async def kick(self, ctx, duser: discord.Member, com):
        if ctx.channel.id == 869510758164201532:
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            user = db.query(User).filter_by(did=duser.id).first()
            if user is None:
                new_user = User(did=ctx.author.id)
                db.add(new_user)
            community = db.query(Community).filter_by(name=com).first()
            if community is None:
                await ctx.send("Community not found or you are not part of that community! Make sure to use the exact shortname.")
            elif user in community.users:
                community.users.remove(user)
                cat = discord.utils.get(guild_ppd.categories, id=int(community.categoryid))
                await cat.set_permissions(duser, read_messages=None, send_messages=None, view_channel=None, speak=None, connect=None)
                for chan in cat.channels:
                    await chan.set_permissions(duser, read_messages=None, send_messages=None, view_channel=None, speak=None, connect=None)
                await ctx.send("Successfully kicked member from community!")
                db.commit()
            else:
                await ctx.send("Community not found or you are not part of that community! Make sure to use the exact shortname.")
        else:
            await ctx.send("Please use B&B Communities #bot-spam")

    @commands.command()
    async def promote(self, ctx, com, member: discord.Member):
        if ctx.channel.id == 869510758164201532:
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            user = db.query(User).filter_by(did=member.id).first()
            community = db.query(Community).filter_by(name=com).first()
            commanduser = db.query(User).filter_by(did=ctx.author.id).first()
            if community is None:
                await ctx.send("Community not found or you have not been invited! Make sure to use the exact shortname.")
            if commanduser in community.admins:
                if user in community.admins:
                    await ctx.send("Already admin")
                else:
                    if user not in community.users:
                        await ctx.send("User not part of community!")
                    else:
                        overwrites = discord.PermissionOverwrite(manage_channels=True, manage_messages=True, move_members=True, mute_members=True, read_messages=True, send_messages=True, view_channel=True, speak=True, connect=True, deafen_members=True)
                        category = guild_ppd.get_channel(community.categoryid)
                        await category.set_permissions(member, overwrite=overwrites)
                        community.users.remove(user)
                        community.admins.append(user)
                        await ctx.send("Member moved to admin.")
                        db.commit()
            else:
                await ctx.send("No Permission!")
        else:
            await ctx.send("Please use B&B Communities #bot-spam")

    @commands.command()
    async def demote(self, ctx, com, member: discord.Member):
        if ctx.channel.id == 869510758164201532:
            guild_ppd = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
            db = Session()
            user = db.query(User).filter_by(did=member.id).first()
            community = db.query(Community).filter_by(name=com).first()
            commanduser = db.query(User).filter_by(did=ctx.author.id).first()
            if community is None:
                await ctx.send("Community not found or you have not been invited! Make sure to use the exact shortname.")
            if commanduser in community.admins:
                if user in community.users:
                    await ctx.send("Already user")
                else:
                    if user not in community.admins:
                        await ctx.send("User not part of community!")
                    else:
                        overwrites = discord.PermissionOverwrite(manage_channels=False, manage_messages=False, move_members=False, mute_members=False, read_messages=True, send_messages=True, view_channel=True, speak=True, connect=True, deafen_members=False)
                        category = guild_ppd.get_channel(community.categoryid)
                        await category.set_permissions(member, overwrite=overwrites)
                        community.admins.remove(user)
                        community.users.append(user)
                        await ctx.send("Member demoted to user.")
                        db.commit()
            else:
                await ctx.send("No Permission!")
        else:
            await ctx.send("Please use B&B Communities #bot-spam")

#main bot definitions
@bot.event
async def on_ready():
    try:
        guild = discord.utils.get(bot.guilds, id=int(guildids["MAIN"]))
        print("Found main guild of ID: "+str(guild.id)+" | Name of: "+str(guild.name))
        print("Members online: "+str(guild.member_count))
    except AttributeError:
        print("Could not find main guild!")
    try:
        guild = discord.utils.get(bot.guilds, id=int(guildids["PPD"]))
        print("Found private plus project discord guild of ID: "+str(guild.id)+" | Name of: "+str(guild.name))
        print("Members online: "+str(guild.member_count))
    except AttributeError:
        print("Could not find private plus project guild!")
    print("Bot's name is "+str(bot.user))

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

#help command
@bot.command()
async def help(ctx):
    embed=discord.Embed(title="Matrix Help", description="These are all the commands available, with Matrix.", color=0x00ff00)
    embed.add_field(name="Music | Basic", value="play 'link or name', pause, resume, nowplaying, seek, queue, remove, skip", inline=False)
    embed.add_field(name="Music | Advanced", value="volume 'level', eq 'band 0-14' 'level -0.25 to 1.0', reseteq", inline=False)
    #embed.add_field(name="Community | Status", value="newcommunity 'name', deletecommunity 'name'", inline=False)
    #embed.add_field(name="Community | Admin", value="invite 'community name' 'member', kick 'member' 'community name', promote 'community name' 'member', demote 'community name' 'member'", inline=False)
    #embed.add_field(name="Community | User", value="accept 'community name', leave 'community name'", inline=False)
    embed.add_field(name="Voice | User", value="voice lock, voice unlock, voice permit 'member', voice reject 'member', voice limit 'number', voice name 'name', voice claim, voice ghost, voice unghost", inline=False)
    embed.add_field(name="Admin", value="voice setup 'channel id' 'category id', voice setlimit 'number', hidecommunity 'name', showcommunity 'name'", inline=False)
    embed.add_field(name="Development", value="shutdown, reload", inline=False)
    await ctx.send(embed=embed)

#run the bot
try:
    #bot.add_cog(PPProject(bot))
    bot.load_extension('voice')
    bot.load_extension('dev')
    bot.load_extension('music')
    bot.run(token)
except KeyboardInterrupt:
    print("Ending")
    bot.close()