import discord
import os
import datetime
from redbot.core import commands, Config, checks

class LoggingCog(commands.Cog):
    """Logt alle berichten, edits, deletes en member events naar logbestanden."""

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
            "channels": []  # leeg = alle kanalen loggen
        }
        self.config.register_guild(**default_guild)

    # -------------------------------
    # Helper functies
    # -------------------------------

    async def get_log_files(self, guild: discord.Guild):
        """Zorgt dat de juiste logfile paden bestaan."""
        settings = await self.config.guild(guild).all()
        log_dir = settings["log_path"]

        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        today = datetime.date.today().strftime("%Y-%m-%d")
        daily_file = os.path.join(log_dir, f"{today}.log")
        history_file = os.path.join(log_dir, "history.log")

        # Zorg dat de bestanden bestaan
        for file in [daily_file, history_file]:
            if not os.path.exists(file):
                with open(file, "a", encoding="utf-8") as f:
                    f.write(f"--- Logging gestart {datetime.datetime.now()} ---\n")

        return daily_file, history_file

    async def log(self, guild: discord.Guild, content: str, timestamp: datetime.datetime = None):
        """Schrijft een regel naar zowel dagbestand als history.log."""
        daily_file, history_file = await self.get_log_files(guild)
        if timestamp is None:
            timestamp = datetime.datetime.now()
        line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} {content}\n"

        for file in [daily_file, history_file]:
            with open(file, "a", encoding="utf-8") as f:
                f.write(line)

    async def is_logged_channel(self, guild: discord.Guild, channel: discord.TextChannel) -> bool:
        settings = await self.config.guild(guild).all()
        if not settings["channels"]:
            return True
        return channel.id in settings["channels"]

    # -------------------------------
    # Events
    # -------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild and not message.author.bot:
            if await self.is_logged_channel(message.guild, message.channel):
                await self.log(
                    message.guild,
                    f"[MESSAGE] #{message.channel} <{message.author}>: {message.content}",
                    timestamp=message.created_at
                )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.guild and not after.author.bot:
            if await self.is_logged_channel(after.guild, after.channel):
                await self.log(
                    after.guild,
                    f"[EDIT] #{after.channel} <{after.author}>: '{before.content}' -> '{after.content}'",
                    timestamp=after.edited_at or after.created_at
                )

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild and not message.author.bot:
            if await self.is_logged_channel(message.guild, message.channel):
                await self.log(
                    message.guild,
                    f"[DELETE] #{message.channel} <{message.author}>: {message.content}",
                    timestamp=message.created_at
                )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.log(member.guild, f"[JOIN] {member} ({member.id})")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.log(member.guild, f"[LEAVE] {member} ({member.id})")

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
        if channel.id in channels:
            channels.remove(channel.id)
            await self.config.guild(ctx.guild).channels.set(channels)
            await ctx.send(f"✅ Kanaal {channel.mention} verwijderd uit logging.")
        else:
            await ctx.send("⚠️ Kanaal staat niet in de lijst.")

    @logset.command()
    async def status(self, ctx):
        """Toon de huidige instellingen."""
        settings = await self.config.guild(ctx.guild).all()
        channels = settings["channels"]
        if not channels:
            ch_text = "Alle kanalen"
        else:
            ch_text = ", ".join(f"<#{c}>" for c in channels)

        await ctx.send(
            f"**Logging status:** {'✅ Aan' if settings['enabled'] else '❌ Uit'}\n"
            f"**Pad:** {settings['log_path']}\n"
            f"**Kanalen:** {ch_text}"
        )

    @logset.command()
    async def harvesthistory(self, ctx):
        """Log de volledige kanaalgeschiedenis in alle ingestelde kanalen."""
        await ctx.send("⏳ Start met ophalen van geschiedenis... Dit kan lang duren!")

        settings = await self.config.guild(ctx.guild).all()
        count = 0

        for channel in ctx.guild.text_channels:
            if not await self.is_logged_channel(ctx.guild, channel):
                continue

            try:
                async for message in channel.history(limit=None, oldest_first=True):
                    if not message.author.bot:
                        await self.log(
                            ctx.guild,
                            f"[HISTORY] #{channel} <{message.author}>: {message.content}",
                            timestamp=message.created_at
                        )
                        count += 1
            except discord.Forbidden:
                await ctx.send(f"⚠️ Geen toegang tot {channel.mention}, overslaan.")
            except discord.HTTPException:
                await ctx.send(f"⚠️ Fout bij ophalen berichten van {channel.mention}, overslaan.")

        await ctx.send(f"✅ Geschiedenis harvesting voltooid. {count} berichten gelogd.")
