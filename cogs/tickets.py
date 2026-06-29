import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import os
import re
from pathlib import Path
from database import DB_PATH

# Константы
ACTIVE_CATEGORY_ID = 1133395829227536394
ARCHIVE_CAT_1 = 1334312861006299157
ARCHIVE_CAT_2 = 1415047244821958676
REVIEW_CHANNEL_ID = 1082039520901468240
LOCAL_BASE_PATH = Path(r"D:\Laker Production\Laker.Design\Orders")

class ReviewModal(discord.ui.Modal, title='Оставить отзыв'):
    review = discord.ui.TextInput(
        label='Ваш отзыв', style=discord.TextStyle.paragraph, required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.review.value:
            review_channel = interaction.guild.get_channel(REVIEW_CHANNEL_ID)
            embed = discord.Embed(description=self.review.value, color=0xFFFFFF)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            await review_channel.send(embed=embed)

        channel = interaction.channel
        guild = interaction.guild

        # Логика архивации
        archive1 = guild.get_channel(ARCHIVE_CAT_1)
        archive2 = guild.get_channel(ARCHIVE_CAT_2)

        if not archive1 and not archive2:
            await interaction.followup.send("Архивные категории не найдены.", ephemeral=True)
            return

        if archive1 and len(archive1.channels) < 50:
            target_category = archive1
        else:
            target_category = archive2
        
        await channel.edit(category=target_category)
        await channel.set_permissions(interaction.user, overwrite=None) # Снятие прав

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.primary, custom_id="persistent_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        guild = interaction.guild

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT ticket FROM client WHERE discord_id = ?", (user.id,)) as cursor:
                row = await cursor.fetchone()
                ticket_channel_id = row[0] if row else None

        active_cat = guild.get_channel(ACTIVE_CATEGORY_ID)
        ticket_channel = guild.get_channel(ticket_channel_id) if ticket_channel_id else None

        # Проверка существующих тикетов
        if ticket_channel:
            if ticket_channel.category_id == ACTIVE_CATEGORY_ID:
                return await interaction.followup.send(f"У вас уже есть активный тикет: {ticket_channel.mention}", ephemeral=True)
            
            # Если в архиве — достаем
            if ticket_channel.category_id in [ARCHIVE_CAT_1, ARCHIVE_CAT_2]:
                await ticket_channel.edit(category=active_cat)
                await ticket_channel.set_permissions(user, read_messages=True, send_messages=True)
                
                embed = discord.Embed(title="--------------------------NEW ORDER--------------------------", color=0xffffff)
                await ticket_channel.send(embed=embed)
                return await interaction.followup.send(f"Ваш старый тикет восстановлен: {ticket_channel.mention}", ephemeral=True)

        # Создание нового тикета
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', user.name)
        channel_name = f"ticket-{clean_name}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        new_channel = await guild.create_text_channel(
            name=channel_name,
            category=active_cat,
            overwrites=overwrites,
            topic=f"Локальная папка: {clean_name}"
        )

        # Создание локальной папки
        folder_path = LOCAL_BASE_PATH / clean_name
        os.makedirs(folder_path, exist_ok=True)

        # Обновление БД
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE client SET ticket = ? WHERE discord_id = ?", (new_channel.id, user.id))
            await db.commit()

        await interaction.followup.send(f"Тикет создан: {new_channel.mention}", ephemeral=True)


class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="close", description="Закрыть текущий тикет")
    async def close_ticket(self, interaction: discord.Interaction):
        # Простая проверка, что команда вызвана в категории тикетов (активной)
        if interaction.channel.category_id != ACTIVE_CATEGORY_ID:
            return await interaction.response.send_message("Эту команду можно использовать только в тикете.", ephemeral=True)
        
        await interaction.response.send_modal(ReviewModal())

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))