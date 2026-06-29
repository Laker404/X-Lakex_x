import discord
from discord.ext import commands, tasks
from datetime import time
from zoneinfo import ZoneInfo
import os
import asyncio
from dotenv import load_dotenv

from database import init_db, sync_member
from cogs.tickets import TicketView

load_dotenv()

# Константы
ROLE_ON_JOIN_ID = 1081958559060869270
TICKET_CHANNEL_ID = 1315592499074695188
MSK_TZ = ZoneInfo("Europe/Moscow")

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await init_db()
        self.add_view(TicketView()) # Регистрация персистентной кнопки
        
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
                
        await self.tree.sync()
        self.daily_sync.start()
        self.loop.create_task(self.startup_routines())

    async def startup_routines(self):
        await self.wait_until_ready()
        await self._sync_all_clients()
        await self._setup_ticket_message()

    async def _sync_all_clients(self):
        """Синхронизация всех пользователей с БД."""
        for guild in self.guilds:
            for member in guild.members:
                if not member.bot:
                    await sync_member(member.id, str(member))

    async def _setup_ticket_message(self):
        """Создание или обновление Embed сообщения для тикетов."""
        channel = self.get_channel(TICKET_CHANNEL_ID)
        if not channel: return

        embed = discord.Embed(
            title="Открыть заказ ✒️",
            description="Нажмите кнопку ниже, чтобы открыть личный канал заявки.\nМы ответим вам в ближайшее время!",
            color=0xffffff
        )
        view = TicketView()

        async for msg in channel.history(limit=10):
            if msg.author == self.user:
                await msg.edit(embed=embed, view=view)
                return
        
        await channel.send(embed=embed, view=view)

    @tasks.loop(time=time(hour=7, minute=0, tzinfo=MSK_TZ))
    async def daily_sync(self):
        """Ежедневная синхронизация БД в 07:00 МСК."""
        await self._sync_all_clients()

bot = MyBot()

@bot.event
async def on_member_join(member: discord.Member):
    await sync_member(member.id, str(member))
    role = member.guild.get_role(ROLE_ON_JOIN_ID)
    if role:
        await member.add_roles(role)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))