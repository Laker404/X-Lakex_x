import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
from database import log_action

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Выгнать пользователя")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await member.kick(reason=reason)
        await log_action("Moderation", f"{interaction.user} kicked {member}. Reason: {reason}")
        await interaction.response.send_message(f"Пользователь {member.mention} выгнан.", ephemeral=True)

    @app_commands.command(name="ban", description="Забанить пользователя")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await member.ban(reason=reason)
        await log_action("Moderation", f"{interaction.user} banned {member}. Reason: {reason}")
        await interaction.response.send_message(f"Пользователь {member.mention} забанен.", ephemeral=True)

    @app_commands.command(name="mute", description="Замутить пользователя")
    @app_commands.default_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        await log_action("Moderation", f"{interaction.user} muted {member} for {minutes}m. Reason: {reason}")
        await interaction.response.send_message(f"Пользователь {member.mention} замучен.", ephemeral=True)

    @app_commands.command(name="warn", description="Выдать предупреждение")
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await log_action("Moderation", f"{interaction.user} warned {member}. Reason: {reason}")
        await interaction.response.send_message(f"{member.mention} получил предупреждение: {reason}")

    # Команды unban, unmute, unwarn реализуются аналогично, снимая timeout/ban и логируя действие.

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))