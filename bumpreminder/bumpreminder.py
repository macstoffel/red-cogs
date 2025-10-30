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
            "last_bump": None,
            "thank_channel_id": None,
            "thank_enabled": True,
            "thank_message": "Thanks for bumping the server, {user}!"
        }
        self.config.register_guild(**default_guild)

    async def _reminder_task(self, guild: discord.Guild, channel_id: int, role_id: int):
        """Background task: wacht 2 uur en stuur reminder."""
        await asyncio.sleep(7200)  # 2 uur
        channel = guild.get_channel(channel_id) if channel_id else None
        role = guild.get_role(role_id) if role_id else None
        if channel and role:
            try:
                await channel.send(f"{role.mention} Tijd om weer te bumpen! 🚀")
            except discord.Forbidden:
                pass

    # ------------------------
    # Activiteit tracken
    # ------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return

        # Als Disboard bevestigt dat een bump succesvol was:
        if message.author.bot and "Bump done" in (message.content or ""):
            # save timestamp
            guild_conf = self.config.guild(message.guild)
            await guild_conf.last_bump.set(datetime.datetime.utcnow().timestamp())

            # stuur onmiddelijke "thank you" als ingeschakeld
            data = await guild_conf.all()
            thank_enabled = data.get("thank_enabled", True)
            thank_channel_id = data.get("thank_channel_id")
            thank_message = data.get("thank_message", "Thanks for bumping the server, {user}!")
            thank_channel = (
                message.guild.get_channel(thank_channel_id) if thank_channel_id else message.channel
            )

            if thank_enabled and thank_channel:
                try:
                    embed = discord.Embed(
                        title="Dankjewel voor het bumpen! 🎉",
                        description=thank_message.format(user=message.author.mention),
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow(),
                    )
                    embed.set_footer(text=f"{message.guild.name} • Bumped")
                    await thank_channel.send(embed=embed)
                except discord.Forbidden:
                    pass

            # start background reminder (non-blocking)
            channel_id = data.get("channel_id")
            role_id = data.get("role_id")
            if channel_id and role_id:
                asyncio.create_task(self._reminder_task(message.guild, channel_id, role_id))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # geen wijziging; niet gebruikt in deze cog, maar placeholder indien gewenst
        return

    # ------------------------
    # Commands
    # ------------------------
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

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def bumpsettings(self, ctx):
        """Toon huidige bump- en thank-you instellingen."""
        data = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(data.get("channel_id")) if data.get("channel_id") else None
        role = ctx.guild.get_role(data.get("role_id")) if data.get("role_id") else None
        thank_channel = ctx.guild.get_channel(data.get("thank_channel_id")) if data.get("thank_channel_id") else None
        thank_enabled = data.get("thank_enabled", True)
        thank_message = data.get("thank_message", "Thanks for bumping the server, {user}!")

        embed = discord.Embed(title="BumpReminder instellingen", color=await ctx.embed_color())
        embed.add_field(name="Reminder kanaal", value=channel.mention if channel else "Niet ingesteld", inline=False)
        embed.add_field(name="Reminder rol", value=role.mention if role else "Niet ingesteld", inline=False)
        embed.add_field(name="Thank-you ingeschakeld", value=str(thank_enabled), inline=False)
        embed.add_field(name="Thank-you kanaal", value=thank_channel.mention if thank_channel else "Stuur naar bump-kanaal", inline=False)
        embed.add_field(name="Thank-you boodschap", value=thank_message, inline=False)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def bumpthanks_setchannel(self, ctx, channel: discord.TextChannel = None):
        """Stel het kanaal in waar de 'thank you' gestuurd wordt. Laat leeg om te verwijderen (stuur naar bump-kanaal)."""
        guild_conf = self.config.guild(ctx.guild)
        await guild_conf.thank_channel_id.set(channel.id if channel else None)
        await ctx.send(f"✅ Thank-you kanaal ingesteld: {channel.mention if channel else 'Stuur naar bump-kanaal'}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def bumpthanks_setmessage(self, ctx, *, message_text: str):
        """Stel de thank-you boodschap in. Gebruik {user} om de beller te mentionen."""
        guild_conf = self.config.guild(ctx.guild)
        await guild_conf.thank_message.set(message_text)
        await ctx.send("✅ Thank-you boodschap opgeslagen.")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def bumpthanks_toggle(self, ctx):
        """Schakel de thank-you berichtgeving aan/uit."""
        guild_conf = self.config.guild(ctx.guild)
        current = await guild_conf.thank_enabled()
        await guild_conf.thank_enabled.set(not current)
        await ctx.send(f"✅ Thank-you berichten {'ingeschakeld' if not current else 'uitgeschakeld'}.")
