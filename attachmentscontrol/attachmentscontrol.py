import discord
from redbot.core import commands, Config
from datetime import datetime, timedelta


class AttachmentsControl(commands.Cog):
    """Configurable attachment anti-spam system"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987654321, force_registration=True)

        default_guild = {
            "enabled": False,
            "role_id": None,
            "max_attachments": 4,
            "time_window": 30,
            "first_timeout_minutes": 30,
            "escalation_hours": 24,
            "escalation_window_minutes": 30,
            "log_channel_id": None
        }

        self.config.register_guild(**default_guild)

        self.user_cache = {}  # {guild_id: {user_id: [timestamps]}}
        self.escalation_flags = {}  # {guild_id: {user_id: expiry}}

    # =======================
    # EVENT LISTENER
    # =======================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        guild_conf = await self.config.guild(message.guild).all()
        if not guild_conf["enabled"]:
            return

        role_id = guild_conf["role_id"]
        if not role_id:
            return

        role = message.guild.get_role(role_id)
        if role not in message.author.roles:
            return

        if not message.attachments:
            return

        now = datetime.utcnow()
        guild_id = message.guild.id
        user_id = message.author.id

        # Init guild cache
        self.user_cache.setdefault(guild_id, {})
        self.escalation_flags.setdefault(guild_id, {})

        # Escalation check
        flag_expiry = self.escalation_flags[guild_id].get(user_id)
        if flag_expiry and now < flag_expiry:
            await self.apply_timeout(
                message,
                guild_conf["escalation_hours"] * 60,
                "Herhaalde attachment spam binnen escalatieperiode"
            )
            return

        # Clean old timestamps
        timestamps = self.user_cache[guild_id].get(user_id, [])
        window = timedelta(seconds=guild_conf["time_window"])
        timestamps = [t for t in timestamps if now - t < window]

        timestamps.append(now)
        self.user_cache[guild_id][user_id] = timestamps

        if len(timestamps) > guild_conf["max_attachments"]:
            # Set escalation flag
            self.escalation_flags[guild_id][user_id] = (
                now + timedelta(minutes=guild_conf["escalation_window_minutes"])
            )

            await self.apply_timeout(
                message,
                guild_conf["first_timeout_minutes"],
                "Te veel attachments in korte tijd"
            )

    # =======================
    # TIMEOUT FUNCTION
    # =======================

    async def apply_timeout(self, message, minutes, reason):
        try:
            await message.author.timeout(timedelta(minutes=minutes), reason=reason)
        except Exception:
            return

        # DM user
        try:
            await message.author.send(
                f"Je bent in timeout gezet voor {minutes} minuten.\nReden: {reason}"
            )
        except Exception:
            pass

        # Log channel
        guild_conf = await self.config.guild(message.guild).all()
        log_channel_id = guild_conf["log_channel_id"]
        if log_channel_id:
            log_channel = message.guild.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(
                    f"🚨 Attachment spam\n"
                    f"Gebruiker: {message.author} ({message.author.id})\n"
                    f"Timeout: {minutes} minuten\n"
                    f"Reden: {reason}"
                )

    # =======================
    # CONFIG COMMANDS
    # =======================

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def attachcontrol(self, ctx):
        """Configuratie voor attachment anti-spam"""
        pass

    @attachcontrol.command()
    async def enable(self, ctx):
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Attachment control ingeschakeld.")

    @attachcontrol.command()
    async def disable(self, ctx):
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Attachment control uitgeschakeld.")

    @attachcontrol.command()
    async def role(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).role_id.set(role.id)
        await ctx.send(f"Rol ingesteld op: {role.name}")

    @attachcontrol.command()
    async def max(self, ctx, amount: int):
        await self.config.guild(ctx.guild).max_attachments.set(amount)
        await ctx.send(f"Max attachments ingesteld op {amount}")

    @attachcontrol.command()
    async def window(self, ctx, seconds: int):
        await self.config.guild(ctx.guild).time_window.set(seconds)
        await ctx.send(f"Tijdvenster ingesteld op {seconds} seconden")

    @attachcontrol.command()
    async def firsttimeout(self, ctx, minutes: int):
        await self.config.guild(ctx.guild).first_timeout_minutes.set(minutes)
        await ctx.send(f"Eerste timeout ingesteld op {minutes} minuten")

    @attachcontrol.command()
    async def escalation(self, ctx, hours: int):
        await self.config.guild(ctx.guild).escalation_hours.set(hours)
        await ctx.send(f"Escalatie timeout ingesteld op {hours} uur")

    @attachcontrol.command()
    async def escalationwindow(self, ctx, minutes: int):
        await self.config.guild(ctx.guild).escalation_window_minutes.set(minutes)
        await ctx.send(f"Escalatieperiode ingesteld op {minutes} minuten")

    @attachcontrol.command()
    async def logchannel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).log_channel_id.set(channel.id)
        await ctx.send(f"Logkanaal ingesteld op {channel.name}")

    @attachcontrol.command(name="show")
    async def show(self, ctx):
        """Toont de huidige configuratie voor deze server."""
        guild_conf = await self.config.guild(ctx.guild).all()

        role = ctx.guild.get_role(guild_conf["role_id"])
        role_name = role.name if role else "Niet ingesteld"

        log_channel = ctx.guild.get_channel(guild_conf["log_channel_id"])
        log_channel_name = log_channel.name if log_channel else "Niet ingesteld"

        embed = discord.Embed(title="Attachment Control Configuratie", color=discord.Color.blue())
        embed.add_field(name="Ingeschakeld", value=str(guild_conf["enabled"]), inline=False)
        embed.add_field(name="Rol", value=role_name, inline=False)
        embed.add_field(name="Max attachments", value=guild_conf["max_attachments"], inline=False)
        embed.add_field(name="Tijdvenster (s)", value=guild_conf["time_window"], inline=False)
        embed.add_field(name="Eerste timeout (min)", value=guild_conf["first_timeout_minutes"], inline=False)
        embed.add_field(name="Escalatie timeout (uur)", value=guild_conf["escalation_hours"], inline=False)
        embed.add_field(name="Escalatieperiode (min)", value=guild_conf["escalation_window_minutes"], inline=False)
        embed.add_field(name="Logkanaal", value=log_channel_name, inline=False)

        await ctx.send(embed=embed)