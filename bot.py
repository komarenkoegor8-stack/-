import discord
from discord.ext import commands
import os

TOKEN = os.environ.get("TOKEN")

MY_ID = 1193115239995166734
ROLE_NAME = "Subscriber"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

class VerifyView(discord.ui.View):
    def __init__(self, user_id, guild_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        
        # Жестко привязываем custom_id для персистентности
        self.approve_btn.custom_id = f"verify_approve:{user_id}:{guild_id}"
        self.reject_btn.custom_id = f"verify_reject:{user_id}:{guild_id}"

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Говорим Дискорду, что мы приняли запрос и думаем (защита от 3 секунд)
        await interaction.response.defer(ephemeral=True)

        if not hasattr(self, 'guild_id'):
            _, user_id, guild_id = button.custom_id.split(":")
            self.user_id, self.guild_id = int(user_id), int(guild_id)

        guild = bot.get_guild(self.guild_id)
        if not guild:
            await interaction.followup.send("❌ Server not found!", ephemeral=True)
            return

        member = guild.get_member(self.user_id)
        role = discord.utils.get(guild.roles, name=ROLE_NAME)

        if not member:
            await interaction.followup.send("❌ User not found on server!", ephemeral=True)
            return

        if not role:
            await interaction.followup.send("❌ Role not found!", ephemeral=True)
            return

        try:
            await member.add_roles(role)
            # Меняем исходное сообщение админа, убирая кнопки, чтобы не нажать дважды
            await interaction.message.edit(content=f"✅ Approved for {member.name}", view=None, embed=interaction.message.embeds[0])
            
            # Отправляем уведомление юзеру
            await member.send(f"✅ Your screenshot has been approved! You've been given the **{ROLE_NAME}** role.")
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to give this role! Check role hierarchy.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if not hasattr(self, 'guild_id'):
            _, user_id, guild_id = button.custom_id.split(":")
            self.user_id, self.guild_id = int(user_id), int(guild_id)

        guild = bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id) if guild else None
        username = member.name if member else f"User ({self.user_id})"

        # Убираем кнопки у админа
        await interaction.message.edit(content=f"❌ Rejected for {username}", view=None, embed=interaction.message.embeds[0])

        if member:
            try:
                await member.send("❌ Your screenshot has been rejected.")
            except discord.Forbidden:
                pass

@bot.event
async def on_ready():
    # Регистрируем пустую View для старых кнопок
    bot.add_view(VerifyView(0, 0)) 
    print(f"✅ Bot is running: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel) and message.attachments:
        guild = None
        for g in bot.guilds:
            member = g.get_member(message.author.id)
            if member:
                guild = g
                break

        if not guild:
            await message.channel.send("❌ You are not on the server!")
            return

        admin = await bot.fetch_user(MY_ID)
        embed = discord.Embed(
            title="📸 New Screenshot",
            description=f"From: **{message.author}** (`{message.author.id}`)",
            color=0x2b2d31
        )
        embed.set_image(url=message.attachments[0].url)

        await admin.send(embed=embed, view=VerifyView(message.author.id, guild.id))
        await message.channel.send("✅ Your screenshot has been sent for review!")

    await bot.process_commands(message)

bot.run(TOKEN)
