
import discord
from discord.ext import commands
import os
import json
from datetime import datetime

class ChannelBackup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "backup_config.json"
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {"channels": {}, "backup_folder": "backups"}
            os.makedirs(self.config["backup_folder"], exist_ok=True)
            self.save_config()

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add_channel(self, ctx, channel: discord.TextChannel, custom_name: str = None):
        self.config["channels"][str(channel.id)] = {"custom_name": custom_name}
        os.makedirs(self.config["backup_folder"], exist_ok=True)
        self.save_config()
        await ctx.send(f"{channel.name} added to backup list with custom name: {custom_name}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove_channel(self, ctx, channel: discord.TextChannel):
        if str(channel.id) in self.config["channels"]:
            del self.config["channels"][str(channel.id)]
            self.save_config()
            await ctx.send(f"{channel.name} removed from backup list.")
        else:
            await ctx.send("Channel not found in backup list.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_backup_folder(self, ctx, folder: str):
        self.config["backup_folder"] = folder
        os.makedirs(folder, exist_ok=True)
        self.save_config()
        await ctx.send(f"Backup folder set to {folder}")

    def get_filepath(self, channel_id: int):
        channel_info = self.config["channels"].get(str(channel_id), {})
        custom_name = channel_info.get("custom_name")
        filename_prefix = custom_name or str(channel_id)
        # ISO week + year for weekly file
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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.backup_message(message)

async def setup(bot):
    await bot.add_cog(ChannelBackup(bot))
