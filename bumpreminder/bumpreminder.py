import discord
from redbot.core import commands, Config
import asyncio
import datetime
import logging

class GetBumpView(discord.ui.View):
    """View met een knop die de gebruiker een ephemeral kopie van /bump geeft."""
    def __init__(self, bump_command: str = "/bump"):
        super().__init__(timeout=None)
        self.bump_command = bump_command

    @discord.ui.button(label="Kopieer /bump", style=discord.ButtonStyle.primary, custom_id="bumpreminder:copy_bump")
    async def copy_bump(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Plak dit in het tekstveld om te bumpen:\n`{self.bump_command}`",
            ephemeral=True,
        )

class BumpReminder(commands.Cog):
    """Stuur automatisch een bump reminder 2 uur na een succesvolle Disboard bump. """

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
        # logger
        self.logger = logging.getLogger("red.bumpreminder")
        # bekende bump-bot ids, voeg meer toe indien nodig
        self.BUMP_BOT_IDS = {302050872383242240}  # Disboard default id
        # houd per-guild geplande reminder tasks zodat we ze kunnen annuleren
        # map guild_id -> (task, scheduled_at_timestamp, delay_seconds)
        self._scheduled_tasks: dict[int, tuple[asyncio.Task, float, int]] = {}

    async def _reminder_task(self, guild: discord.Guild, channel_id: int, role_id: int, delay: int = 7200, scheduled_at: float = None):
        """Background task: wacht delay seconden en stuur reminder.
        Controleert voor het verzenden of last_bump nog gelijk is aan scheduled_at.
        """
        self.logger.debug("Reminder task started for guild %s, channel %s, role %s, delay=%s", guild.id, channel_id, role_id, delay)
        try:
            await asyncio.sleep(delay)
            # check of er niet intussen een nieuwe bump is geweest
            guild_conf = self.config.guild(guild)
            current_last = await guild_conf.last_bump()
            if scheduled_at is not None and current_last != scheduled_at:
                self.logger.info("Reminder aborted for guild %s: new bump occurred after scheduling (scheduled_at=%s current_last=%s)", guild.id, scheduled_at, current_last)
                return
            channel = guild.get_channel(channel_id) if channel_id else None
            role = guild.get_role(role_id) if role_id else None
            if channel and role:
                try:
                    reminder_text = f"{role.mention} Tijd om weer te bumpen! 🚀 Gebruik `/bump` in het tekstveld om te bumpen."
                    # stuur reminder mét knop die een ephemeral /bump hint teruggeeft
                    await channel.send(reminder_text, view=GetBumpView("/bump"))
                    self.logger.info("Sent bump reminder in guild %s channel %s", guild.id, channel_id)
                except discord.Forbidden:
                    self.logger.warning("Missing permission to send reminder in guild %s channel %s", guild.id, channel_id)
                except Exception as e:
                    self.logger.exception("Failed to send reminder: %s", e)
            else:
                self.logger.debug("Reminder aborted: channel or role missing (channel=%s role=%s)", channel, role)
        finally:
            # opruimen van taak-registratie
            try:
                tinfo = self._scheduled_tasks.get(guild.id)
                if tinfo and tinfo[0] is asyncio.current_task():
                    self._scheduled_tasks.pop(guild.id, None)
            except Exception:
                self._scheduled_tasks.pop(guild.id, None)

    # ------------------------
    # Activiteit tracken
    # ------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return

        # load guild config early to restrict operation to configured channel
        guild_conf = self.config.guild(message.guild)
        cfg = await guild_conf.all()
        configured_channel_id = cfg.get("channel_id")

        # Only react to messages in the configured reminder channel (if set)
        if configured_channel_id and message.channel.id != configured_channel_id:
            return

        # Ignore other bots (only accept messages from known bump-bots)
        if message.author.bot and getattr(message.author, "id", None) not in self.BUMP_BOT_IDS:
            return

        # debug log every message (can be noisy; keep at debug level)
        self.logger.debug("on_message guild=%s author=%s bot=%s channel=%s content_len=%s embeds=%s",
                          getattr(message.guild, "id", None),
                          getattr(message.author, "id", None),
                          message.author.bot,
                          getattr(message.channel, "id", None),
                          len(message.content or ""),
                          len(message.embeds or []))

        # Robuuste bump-detectie:
        is_bump = False
        # 1) author is known bump bot
        if message.author and getattr(message.author, "id", None) in self.BUMP_BOT_IDS:
            is_bump = True
            self.logger.debug("Detected bump by known bot id %s", message.author.id)
        # 2) content contains bump done (case-insensitive)
        if not is_bump and message.content and "bump" in message.content.lower():
            if "done" in message.content.lower() or "bumped" in message.content.lower():
                is_bump = True
                self.logger.debug("Detected bump by message content")
        # 3) embed title/description contains bump keywords
        if not is_bump and message.embeds:
            for e in message.embeds:
                try:
                    title = (e.title or "").lower()
                    desc = (e.description or "").lower()
                    if "bump" in title or "bump" in desc or "bumped" in title or "bumped" in desc or "bump done" in title or "bump done" in desc:
                        is_bump = True
                        self.logger.debug("Detected bump by embed content")
                        break
                except Exception:
                    continue

        if not is_bump:
            return

        self.logger.info("Processing bump event in guild %s by author %s", message.guild.id, message.author.id)

        # save timestamp
        scheduled_at = datetime.datetime.utcnow().timestamp()
        await guild_conf.last_bump.set(scheduled_at)

        # stuur onmiddelijke "thank you" als ingeschakeld
        thank_enabled = cfg.get("thank_enabled", True)
        thank_channel_id = cfg.get("thank_channel_id")
        thank_message = cfg.get("thank_message", "Thanks for bumping the server, {user}!")
        thank_channel = (
            message.guild.get_channel(thank_channel_id) if thank_channel_id else message.channel
        )

        if thank_enabled and thank_channel:
            try:
                # show the embed timestamp 1 hour later
                embed_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                embed = discord.Embed(
                    title="Dankjewel voor het bumpen! 🎉",
                    description=thank_message.format(user=message.author.mention) + "\n\nOver twee uurtjes kun je weer opnieuw bumpen.",
                    color=discord.Color.green(),
                    timestamp=embed_time,
                )
                embed.set_footer(text=f"{message.guild.name} • Bumped")
                await thank_channel.send(embed=embed)
                self.logger.info("Sent thank-you embed in guild %s channel %s", message.guild.id, thank_channel.id)
            except discord.Forbidden:
                self.logger.warning("Missing permission to send thank-you in guild %s channel %s", message.guild.id, thank_channel.id)
            except Exception as e:
                self.logger.exception("Failed sending thank-you: %s", e)

        # start background reminder (non-blocking) — annuleer vorige als die nog loopt
        channel_id = cfg.get("channel_id")
        role_id = cfg.get("role_id")
        if channel_id and role_id:
            # cancel existing
            existing = self._scheduled_tasks.get(message.guild.id)
            if existing and not existing[0].done():
                existing[0].cancel()
                self.logger.debug("Cancelled existing reminder task for guild %s", message.guild.id)
            task = asyncio.create_task(self._reminder_task(message.guild, channel_id, role_id, delay=7200, scheduled_at=scheduled_at))
            self._scheduled_tasks[message.guild.id] = (task, scheduled_at, 7200)
        else:
            self.logger.debug("Reminder not scheduled: channel_id or role_id not configured for guild %s", message.guild.id)

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

    # --- Test / debug commands ---

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def bumpdebug(self, ctx):
        """Toon huidige instellingen en last_bump (debug)."""
        data = await self.config.guild(ctx.guild).all()
        last_bump_ts = data.get("last_bump")
        last_bump_human = (
            datetime.datetime.utcfromtimestamp(last_bump_ts).isoformat() + " UTC" if last_bump_ts else "No record"
        )
        await ctx.send(
            box := (
                "BumpReminder debug:\n"
                f"channel_id: {data.get('channel_id')}\n"
                f"role_id: {data.get('role_id')}\n"
                f"thank_channel_id: {data.get('thank_channel_id')}\n"
                f"thank_enabled: {data.get('thank_enabled')}\n"
                f"thank_message: {data.get('thank_message')}\n"
                f"last_bump: {last_bump_human}\n"
            )
        )

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def bumptest(self, ctx, delay: int = 10):
        """Test de thank-you + reminder flow. delay = seconden voordat reminder gestuurd wordt (default 10s).
        Geeft ook aan wanneer er weer gebumpt kan worden (next bump time).
        """
        guild_conf = self.config.guild(ctx.guild)
        data = await guild_conf.all()
        thank_enabled = data.get("thank_enabled", True)
        thank_channel_id = data.get("thank_channel_id")
        thank_message = data.get("thank_message", "Thanks for bumping the server, {user}!")
        thank_channel = ctx.guild.get_channel(thank_channel_id) if thank_channel_id else ctx.channel

        # update last_bump and schedule reminder; cancel previous
        scheduled_at = datetime.datetime.utcnow().timestamp()
        await guild_conf.last_bump.set(scheduled_at)

        existing = self._scheduled_tasks.get(ctx.guild.id)
        if existing and not existing[0].done():
            # test already scheduled -> inform and refuse to schedule another
            scheduled_at_existing = existing[1]
            delay_existing = existing[2]
            next_allowed_ts_existing = scheduled_at_existing + delay_existing
            next_allowed_dt_existing = datetime.datetime.utcfromtimestamp(next_allowed_ts_existing)
            remaining_existing = max(0, int((next_allowed_dt_existing - datetime.datetime.utcnow()).total_seconds()))
            hrs_e, rem_e = divmod(remaining_existing, 3600)
            mins_e, secs_e = divmod(rem_e, 60)
            remaining_str_existing = f"{hrs_e}h {mins_e}m {secs_e}s"
            await ctx.send(
                f"⚠️ Er staat al een test/reminder gepland. Volgende bump mogelijk op (UTC): {next_allowed_dt_existing.isoformat()} — over {remaining_str_existing}.\n"
                "Wacht tot die afloopt of annuleer de geplande reminder eerst."
            )
            return

        # schedule with provided delay
        channel_id = data.get("channel_id")
        role_id = data.get("role_id")
        if channel_id and role_id:
            task = asyncio.create_task(self._reminder_task(ctx.guild, channel_id, role_id, delay=delay, scheduled_at=scheduled_at))
            self._scheduled_tasks[ctx.guild.id] = (task, scheduled_at, delay)

        # send immediate confirmation and next-bump-time info
        # NOTE: show next bump time 1 hour later than the reminder time
        next_allowed_ts = scheduled_at + delay + 3600
        next_allowed_dt = datetime.datetime.utcfromtimestamp(next_allowed_ts)
        # human readable remaining time
        remaining = next_allowed_dt - datetime.datetime.utcnow()
        # clamp
        remaining_seconds = max(0, int(remaining.total_seconds()))
        hrs, rem = divmod(remaining_seconds, 3600)
        mins, secs = divmod(rem, 60)
        remaining_str = f"{hrs}h {mins}m {secs}s"

        await ctx.send(
            f"✅ Simulated bump recorded; thank-you sent and reminder scheduled in {delay} seconds.\n"
            f"Volgende bump mogelijk op (UTC): {next_allowed_dt.isoformat()} — over {remaining_str}."
        )

# module setup
async def setup(bot):
    await bot.add_cog(BumpReminder(bot))
