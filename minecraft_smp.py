#  Copyright 2023 Macauley Lim xmachd@gmail.com
#  This code is licensed under GNU AFFERO GENERAL PUBLIC LICENSE v3.0.
#  A copy of this license should have been provided with the code download, if not see https://www.gnu.org/licenses/
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU AGPL v3.0 for more details.
import discord.ext.commands
from sqlalchemy import String, Float, Boolean, create_engine, Integer
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, Session


class Base(DeclarativeBase):
    pass


class MinecraftSMPUsers(Base):
    __tablename__ = "minecraft_smp_users"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    health_max: Mapped[float] = mapped_column(Float())
    dead: Mapped[bool] = mapped_column(Boolean())
    death_message: Mapped[str] = mapped_column(String(255))


class MinecraftSMPServers(Base):
    __tablename__ = "minecraft_smp_servers"
    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(Integer())
    message_id: Mapped[int] = mapped_column(Integer())


class MinecraftSMP:
    def __init__(self, bot):
        self.db = create_engine("sqlite:///smp.db")
        Base.metadata.create_all(self.db)
        self.bot: discord.ext.commands.Bot = bot

    def generate_embed(self) -> discord.Embed:
        embed = discord.Embed(title="BNB Hardcore Survival Player List")

        with Session(self.db) as session:
            users = session.query(MinecraftSMPUsers).all()
            for user in users:
                embed.add_field(
                    name=f"{user.name} - {'Dead' if user.dead else f'{user.health_max}/20.0'} {f'({user.death_message})' if user.dead else ''}",
                    value="")

        return embed

    async def update_message(self):
        with Session(self.db) as session:
            message = session.get(MinecraftSMPServers, 1)
            msg = await self.bot.get_channel(message.channel_id).fetch_message(message.message_id)
            await msg.edit(embed=self.generate_embed(), content="")

    async def new_user(self, uuid, name):
        with Session(self.db) as session:
            user = MinecraftSMPUsers(name=name, health_max=20.0, id=uuid, dead=False, death_message="")
            session.add(user)
            session.commit()
        await self.update_message()

    async def user_death(self, uuid, health_max, dead, death_message):
        with Session(self.db) as session:
            player = session.get(MinecraftSMPUsers, uuid)
            player.health_max = float(health_max)
            player.dead = True if dead == "true" else False
            player.death_message = death_message
            session.commit()
        await self.update_message()

    async def add_message(self, msg_id, chan_id):
        with Session(self.db) as session:
            server = MinecraftSMPServers(message_id=msg_id, channel_id=chan_id)
            session.add(server)
            session.commit()
        await self.update_message()

    async def reset(self):
        with Session(self.db) as session:
            session.query(MinecraftSMPUsers).delete()
            session.commit()
        await self.update_message()
