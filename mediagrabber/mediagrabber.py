import discord
import aiohttp
import os
from redbot.core import commands, Config

class MediaGrabber(commands.Cog):
    """Automatically save uploaded media to a local folder."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_global = {
            "save_path": os.path.join(os.getcwd(), "downloads"),
            "all_channels": False,
            "channels": []
        }
        self.config.register_global(**default_global)

    async def _download_attachment(self, attachment, save_path):
        file_path = os.path.join(save_path, attachment.filename)
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await resp.read())
                    print(f"[MediaGrabber] Saved {attachment.filename}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.attachments:
            return

        all_channels = await self.config.all_channels()
        channels = await self.config.channels()
        save_path = await self.config.save_path()

        # Check if we should save from this channel
        if not all_channels and message.channel.id not in channels:
            return

        os.makedirs(save_path, exist_ok=True)
        for attachment in message.attachments:
            await self._download_attachment(attachment, save_path)

    # ---------------- Commands ---------------- #

    @commands.group()
    async def mediagrabber(self, ctx):
        """Manage media grabber settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @mediagrabber.command()
    async def setpath(self, ctx, *, path: str):
        """Set the folder where media will be saved."""
        await self.config.save_path.set(path)
        os.makedirs(path, exist_ok=True)
        await ctx.send(f"✅ Media will now be saved to: `{path}`")

    @mediagrabber.command()
    async def enableall(self, ctx, toggle: bool):
        """Enable or disable saving from all channels."""
        await self.config.all_channels.set(toggle)
        state = "enabled" if toggle else "disabled"
        await ctx.send(f"✅ Saving from **all channels** {state}.")

    @mediagrabber.command()
    async def addchannel(self, ctx, channel: discord.TextChannel):
        """Add a specific channel to media saving."""
        async with self.config.channels() as chans:
            if channel.id not in chans:
                chans.append(channel.id)
        await ctx.send(f"✅ Added {channel.mention} to the media save list.")

    @mediagrabber.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        """Remove a specific channel from media saving."""
        async with self.config.channels() as chans:
            if channel.id in chans:
                chans.remove(channel.id)
        await ctx.send(f"✅ Removed {channel.mention} from the media save list.")

    @mediagrabber.command()
    async def status(self, ctx):
        """Show current media grabber settings."""
        path = await self.config.save_path()
        all_channels = await self.config.all_channels()
        channels = await self.config.channels()

        channel_mentions = []
        for cid in channels:
            chan = self.bot.get_channel(cid)
            channel_mentions.append(chan.mention if chan else f"`{cid}`")

        msg = (
            f"📂 **Save Path:** `{path}`\n"
            f"🌍 **All Channels:** {all_channels}\n"
            f"📌 **Specific Channels:** {', '.join(channel_mentions) if channel_mentions else 'None'}"
        )
        await ctx.send(msg)
