import discord
from redbot.core import commands
import os
import json
from datetime import datetime
from redbot.core import data_manager

class ChannelBackup(commands.Cog):
    """Backup Discord text channels to local markdown files, auto-updates on new messages."""

    def __init__(self, bot):
        self.bot = bot
        self.config_file = os.path.join(data_manager.cog_data_path(self), "backup_config.json")
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
        else:
            default_folder = os.path.join(data_manager.cog_data_path(self), "backups")
            self.config = {"channels": {}, "backup_folder": default_folder}
            os.makedirs(self.config["backup_folder"], exist_ok=True)
            self.save_config()

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def get_filepath(self, channel_id: int):
        channel_info = self.config["channels"].get(str(channel_id), {})
        custom_name = channel_info.get("custom_name")
        filename_prefix = custom_name or str(channel_id)
        year, week, _ = datetime.utcnow().isocalendar()
        filename = f"{filename_prefix}_week{week}_{year}.md"
        return os.path.join(self.config["backup_folder"], filename)

    async def backup_message(self, message: discord.Message):
        if str(message.channel.id) not in self.config["channels"]:
            return
        filepath = self.get_filepath(message.channel.id)
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        line = f"**{message.author}** [{timestamp}]: {message.content}\n\n"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(line)

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def channelbackup(self, ctx):
        """ChannelBackup configuratie commando's."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @channelbackup.command()
    async def add(self, ctx, channel: discord.TextChannel, custom_name: str = None):
        """Voeg een kanaal toe aan de backup lijst."""
        self.config["channels"][str(channel.id)] = {"custom_name": custom_name}
        os.makedirs(self.config["backup_folder"], exist_ok=True)
        self.save_config()
        await ctx.send(f"{channel.name} toegevoegd aan backup lijst met naam: {custom_name or channel.name}")

    @channelbackup.command()
    async def remove(self, ctx, channel: discord.TextChannel):
        """Verwijder een kanaal uit de backup lijst."""
        if str(channel.id) in self.config["channels"]:
            del self.config["channels"][str(channel.id)]
            self.save_config()
            await ctx.send(f"{channel.name} verwijderd uit backup lijst.")
        else:
            await ctx.send("Kanaal niet gevonden in backup lijst.")

    @channelbackup.command()
    async def setfolder(self, ctx, folder: str):
        """Stel de backup folder in."""
        self.config["backup_folder"] = folder
        os.makedirs(folder, exist_ok=True)
        self.save_config()
        await ctx.send(f"Backup folder ingesteld op: {folder}")

    @channelbackup.command()
    async def status(self, ctx):
        """Toon huidige backup instellingen."""
        folder = self.config["backup_folder"]
        channels = self.config["channels"]
        channel_list = []
        for cid, info in channels.items():
            chan = self.bot.get_channel(int(cid))
            name = info.get("custom_name") or (chan.name if chan else cid)
            channel_list.append(f"{name} (`{cid}`)")
        msg = (
            f"**Backup folder:** `{folder}`\n"
            f"**Kanalen:** {', '.join(channel_list) if channel_list else 'Geen'}"
        )
        await ctx.send(msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.backup_message(message)

async def setup(bot):
    await bot.add_cog(ChannelBackup(bot))
