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

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)
        role = discord.utils.get(guild.roles, name=ROLE_NAME)

        if not member:
            await interaction.response.send_message("❌ User not found on server!", ephemeral=True)
            return

        if not role:
            await interaction.response.send_message("❌ Role not found!", ephemeral=True)
            return

        await member.add_roles(role)
        await interaction.response.send_message(f"✅ {member.name} has been approved and given the {ROLE_NAME} role!")

        # Notify the user
        await member.send(f"✅ Your screenshot has been approved! You've been given the **{ROLE_NAME}** role.")
        self.stop()

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)

        await interaction.response.send_message(f"❌ {member.name} has been rejected.")

        # Notify the user
        await member.send("❌ Your screenshot has been rejected.")
        self.stop()

@bot.event
async def on_ready():
    print(f"✅ Bot is running: {bot.user}")

@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    # Only handle DMs with attachments
    if isinstance(message.channel, discord.DMChannel) and message.attachments:
        # Find the guild
        guild = None
        for g in bot.guilds:
            member = g.get_member(message.author.id)
            if member:
                guild = g
                break

        if not guild:
            await message.channel.send("❌ You are not on the server!")
            return

        # Forward to admin
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
