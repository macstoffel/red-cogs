import discord
from redbot.core import commands, Config
import asyncio
import datetime

class BumpReminder(commands.Cog):
    """Stuur automatisch een bump reminder 2 uur na een succesvolle Disboard bump."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channel_id": None,
            "role_id": None,
            "last_bump": None
        }
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return

        # Als Disboard bevestigt dat een bump succesvol was:
        if message.author.bot and "Bump done" in message.content:
            guild_conf = self.config.guild(message.guild)

            # tijd opslaan
            await guild_conf.last_bump.set(datetime.datetime.utcnow().timestamp())

            # wachten (7200s = 2 uur)
            await asyncio.sleep(7200)

            data = await guild_conf.all()
            channel = message.guild.get_channel(data["channel_id"])
            role = message.guild.get_role(data["role_id"])

            if channel and role:
                try:
                    await channel.send(f"{role.mention} Tijd om weer te bumpen! 🚀")
                except discord.Forbidden:
                    pass  # Geen rechten om te posten? Dan crashen we niet.

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def bumpset(self, ctx, channel: discord.TextChannel, role: discord.Role):
        """Stel reminder-kanaal en rol in. Voorbeeld: [p]bumpset #bump @Bumpers"""
        guild_conf = self.config.guild(ctx.guild)

        await guild_conf.channel_id.set(channel.id)
        await guild_conf.role_id.set(role.id)

        await ctx.send(
            f"✅ Bump reminders ingesteld.\n"
            f"📨 Kanaal: {channel.mention}\n"
            f"🔔 Rol: {role.mention}"
        )
