import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from database import DB_PATH

class EmbedModal(discord.ui.Modal, title='Создание Embed'):
    content = discord.ui.TextInput(
        label='Текст сообщения',
        style=discord.TextStyle.paragraph,
        placeholder='Введите текст...',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(description=self.content.value, color=0xffffff)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=f"by @{interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message("Embed успешно отправлен.", ephemeral=True)
        await interaction.channel.send(embed=embed)

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server", description="Статистика сервера")
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"Сервер: {guild.name}", color=discord.Color.blue())
        embed.add_field(name="Участников", value=guild.member_count)
        embed.add_field(name="Создан", value=guild.created_at.strftime("%d.%m.%Y"))
        embed.add_field(name="Бусты", value=guild.premium_subscription_count)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="client", description="Статистика пользователя из БД")
    async def client_info(self, interaction: discord.Interaction, user: discord.Member):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT discord_tag, status, discount, order_count FROM client WHERE discord_id = ?", (user.id,)) as cursor:
                row = await cursor.fetchone()
                
        if not row:
            return await interaction.response.send_message("Пользователь не найден в БД.", ephemeral=True)

        embed = discord.Embed(title=f"Клиент: {row[0]}", color=discord.Color.green())
        embed.add_field(name="Статус", value=row[1])
        embed.add_field(name="Скидка", value=f"{row[2]}%")
        embed.add_field(name="Заказов", value=row[3])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="embed", description="Создать кастомный Embed")
    async def create_embed(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmbedModal())

async def setup(bot):
    await bot.add_cog(InfoCog(bot))