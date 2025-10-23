import discord
import os
import datetime
import glob
from redbot.core import commands, Config, checks

class LoggingCog(commands.Cog):
    """Logt alle berichten, edits, deletes en member events naar per-kanaal logbestanden."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=1234567890,
            force_registration=True
        )
        default_guild = {
            "enabled": True,
            "log_path": "./logs",
            "channels": None  # None = alle kanalen, [] = geen kanalen
        }
        self.config.register_guild(**default_guild)

    # -------------------------------
    # Helper functies
    # -------------------------------

    def get_channel_log_file(self, log_dir, channel: discord.TextChannel, suffix=""):
        """Geeft het pad voor een kanaal-logbestand."""
        safe_name = channel.name.replace("/", "_").replace("\\", "_")
        return os.path.join(log_dir, f"{safe_name}{suffix}.log")

    def get_channel_daily_log_file(self, log_dir, channel: discord.TextChannel, date: datetime.date):
        """Geeft het pad voor een kanaal-daglogbestand."""
        safe_name = channel.name.replace("/", "_").replace("\\", "_")
        return os.path.join(log_dir, f"{safe_name}_{date.isoformat()}.log")

    async def log(self, guild: discord.Guild, channel: discord.TextChannel, content: str, timestamp: datetime.datetime = None, suffix=""):
        """Schrijft een regel naar het kanaal-daglogbestand én naar een centrale logfile. Houdt max 2 daglogs per kanaal."""
        settings = await self.config.guild(guild).all()
        log_dir = settings["log_path"]

        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Gebruik daglog per kanaal
        log_file = self.get_channel_daily_log_file(log_dir, channel, (timestamp or datetime.datetime.now()).date())
        central_file = os.path.join(log_dir, "all_channels.log")

        # Daglog cleanup: max 2 per kanaal
        safe_name = channel.name.replace("/", "_").replace("\\", "_")
        pattern = os.path.join(log_dir, f"{safe_name}_*.log")
        files = sorted(glob.glob(pattern))
        if len(files) > 2:
            for oldfile in files[:-2]:
                os.remove(oldfile)

        if not os.path.exists(log_file):
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"--- Logging gestart {datetime.datetime.now()} ---\n")
        if not os.path.exists(central_file):
            with open(central_file, "a", encoding="utf-8") as f:
                f.write(f"--- Centrale logging gestart {datetime.datetime.now()} ---\n")

        if timestamp is None:
            timestamp = datetime.datetime.now()
        line = f"[{timestamp.strftime('%H:%M:%S')}] #{channel.name} {content}\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
        with open(central_file, "a", encoding="utf-8") as f:
            f.write(line)

    async def is_logged_channel(self, guild: discord.Guild, channel: discord.TextChannel) -> bool:
        settings = await self.config.guild(guild).all()
        channels = settings["channels"]
        if channels is None:  # alle kanalen
            return True
        if channels == []:  # geen kanalen
            return False
        return channel.id in channels

    # -------------------------------
    # Events
    # -------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild and not message.author.bot:
            if await self.is_logged_channel(message.guild, message.channel):
                await self.log(
                    message.guild,
                    message.channel,
                    f"[MESSAGE] <{message.author}> {message.content}",
                    timestamp=message.created_at
                )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.guild and not after.author.bot:
            if await self.is_logged_channel(after.guild, after.channel):
                await self.log(
                    after.guild,
                    after.channel,
                    f"[EDIT] <{after.author}> '{before.content}' -> '{after.content}'",
                    timestamp=after.edited_at or after.created_at
                )

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild and not message.author.bot:
            if await self.is_logged_channel(message.guild, message.channel):
                await self.log(
                    message.guild,
                    message.channel,
                    f"[DELETE] <{message.author}> {message.content}",
                    timestamp=message.created_at
                )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Log naar elk kanaal dat gelogd wordt
        guild = member.guild
        settings = await self.config.guild(guild).all()
        log_dir = settings["log_path"]
        for channel in guild.text_channels:
            if await self.is_logged_channel(guild, channel):
                await self.log(guild, channel, f"[JOIN] <{member}> ({member.id})")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        settings = await self.config.guild(guild).all()
        log_dir = settings["log_path"]
        for channel in guild.text_channels:
            if await self.is_logged_channel(guild, channel):
                await self.log(guild, channel, f"[LEAVE] <{member}> ({member.id})")

    # -------------------------------
    # Commands
    # -------------------------------

    @commands.group()
    @checks.admin()
    async def logset(self, ctx):
        """Instellingen voor logging beheren."""
        pass

    @logset.command()
    async def toggle(self, ctx):
        """Logging aan/uit schakelen."""
        enabled = await self.config.guild(ctx.guild).enabled()
        await self.config.guild(ctx.guild).enabled.set(not enabled)
        await ctx.send(f"✅ Logging {'ingeschakeld' if not enabled else 'uitgeschakeld'}.")

    @logset.command()
    async def path(self, ctx, *, path: str):
        """Stel de map in waar logs opgeslagen worden."""
        await self.config.guild(ctx.guild).log_path.set(path)
        await ctx.send(f"✅ Logpad ingesteld op: `{path}`")

    @logset.command()
    async def addchannel(self, ctx, channel: discord.TextChannel):
        """Voeg een kanaal toe aan logging."""
        channels = await self.config.guild(ctx.guild).channels()
        if channels is None:
            channels = []
        if channel.id not in channels:
            channels.append(channel.id)
            await self.config.guild(ctx.guild).channels.set(channels)
            await ctx.send(f"✅ Kanaal {channel.mention} toegevoegd aan logging.")
        else:
            await ctx.send("⚠️ Kanaal staat al in de lijst.")

    @logset.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        """Verwijder een kanaal uit logging."""
        channels = await self.config.guild(ctx.guild).channels()
        if channels and channel.id in channels:
            channels.remove(channel.id)
            await self.config.guild(ctx.guild).channels.set(channels)
            await ctx.send(f"✅ Kanaal {channel.mention} verwijderd uit logging.")
        else:
            await ctx.send("⚠️ Kanaal staat niet in de lijst.")

    @logset.command()
    async def clearchannels(self, ctx):
        """Verwijder alle kanalen uit logging (niets wordt gelogd)."""
        await self.config.guild(ctx.guild).channels.set([])
        await ctx.send("✅ Alle kanalen verwijderd uit logging. Er wordt nu niets gelogd.")

    @logset.command()
    async def allchannels(self, ctx):
        """Reset logging naar alle kanalen."""
        await self.config.guild(ctx.guild).channels.set(None)
        await ctx.send("✅ Logging ingesteld op alle kanalen.")

    @logset.command()
    async def status(self, ctx):
        """Toon de huidige instellingen."""
        settings = await self.config.guild(ctx.guild).all()
        channels = settings["channels"]

        if channels is None:
            ch_text = "Alle kanalen"
        elif channels == []:
            ch_text = "Geen kanalen"
        else:
            ch_text = ", ".join(f"<#{c}>" for c in channels)

        await ctx.send(
            f"**Logging status:** {'✅ Aan' if settings['enabled'] else '❌ Uit'}\n"
            f"**Pad:** {settings['log_path']}\n"
            f"**Kanalen:** {ch_text}"
        )

    @logset.command()
    async def harvesthistory(self, ctx):
        """Log de volledige kanaalgeschiedenis in alle ingestelde kanalen (per kanaalbestand)."""
        await ctx.send("⏳ Start met ophalen van kanaalgeschiedenis... Dit kan lang duren!")

        count = 0
        for channel in ctx.guild.text_channels:
            if not await self.is_logged_channel(ctx.guild, channel):
                continue

            settings = await self.config.guild(ctx.guild).all()
            log_dir = settings["log_path"]
            history_file = self.get_channel_log_file(log_dir, channel, "_history")

            # Zorg dat het bestand bestaat
            if not os.path.exists(history_file):
                with open(history_file, "a", encoding="utf-8") as f:
                    f.write(f"--- History harvesting gestart {datetime.datetime.now()} ---\n")

            try:
                async for message in channel.history(limit=None, oldest_first=True):
                    if not message.author.bot:
                        line = f"[{message.created_at.strftime('%H:%M:%S')}] <{message.author}> {message.content}\n"
                        with open(history_file, "a", encoding="utf-8") as f:
                            f.write(line)
                        count += 1
            except discord.Forbidden:
                await ctx.send(f"⚠️ Geen toegang tot {channel.mention}, overslaan.")
            except discord.HTTPException:
                await ctx.send(f"⚠️ Fout bij ophalen berichten van {channel.mention}, overslaan.")

        await ctx.send(f"✅ Geschiedenis harvesting voltooid. {count} berichten gelogd.")

    @logset.command()
    async def harvestchannel(self, ctx, channel: discord.TextChannel):
        """Log de volledige geschiedenis van één kanaal (in apart history-bestand)."""
        if not await self.is_logged_channel(ctx.guild, channel):
            await ctx.send("⚠️ Dit kanaal staat niet op de logginglijst.")
            return

        settings = await self.config.guild(ctx.guild).all()
        log_dir = settings["log_path"]
        history_file = self.get_channel_log_file(log_dir, channel, "_history")

        if not os.path.exists(history_file):
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(f"--- History harvesting gestart {datetime.datetime.now()} ---\n")

        count = 0
        await ctx.send(f"⏳ Start met ophalen van geschiedenis uit {channel.mention}...")
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                if not message.author.bot:
                    line = f"[{message.created_at.strftime('%H:%M:%S')}] <{message.author}> {message.content}\n"
                    with open(history_file, "a", encoding="utf-8") as f:
                        f.write(line)
                    count += 1
        except discord.Forbidden:
            await ctx.send(f"⚠️ Geen toegang tot {channel.mention}.")
        except discord.HTTPException:
            await ctx.send(f"⚠️ Fout bij ophalen berichten van {channel.mention}.")

        await ctx.send(f"✅ Geschiedenis harvesting voltooid voor {channel.mention}. {count} berichten gelogd.")