import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class VoicePing(commands.Cog):
    """Ping a text channel when someone joins a voice channel, with exclusions."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987654321)
        default_guild = {
            "text_channel_id": None,
            "excluded_voice_ids": []
        }
        self.config.register_guild(**default_guild)

    @commands.group()
    @commands.admin()
    async def voiceping(self, ctx):
        """VoicePing configuration."""
        pass

    @voiceping.command()
    async def settextchannel(self, ctx, text_channel: discord.TextChannel):
        """Set the text channel where pings will be sent."""
        await self.config.guild(ctx.guild).text_channel_id.set(text_channel.id)
        await ctx.send(f"✅ Text channel set to {text_channel.mention}.")

    @voiceping.command()
    async def addexclude(self, ctx, voice_channel: discord.VoiceChannel):
        """Exclude a voice channel from pinging."""
        excluded = await self.config.guild(ctx.guild).excluded_voice_ids()
        if voice_channel.id in excluded:
            await ctx.send("⚠️ That channel is already excluded.")
            return
        excluded.append(voice_channel.id)
        await self.config.guild(ctx.guild).excluded_voice_ids.set(excluded)
        await ctx.send(f"🚫 Excluded {voice_channel.mention} from pinging.")

    @voiceping.command()
    async def removeexclude(self, ctx, voice_channel: discord.VoiceChannel):
        """Remove a voice channel from the exclusion list."""
        excluded = await self.config.guild(ctx.guild).excluded_voice_ids()
        if voice_channel.id not in excluded:
            await ctx.send("⚠️ That channel is not excluded.")
            return
        excluded.remove(voice_channel.id)
        await self.config.guild(ctx.guild).excluded_voice_ids.set(excluded)
        await ctx.send(f"✅ {voice_channel.mention} is no longer excluded.")

    @voiceping.command(name="listexcluded")
    async def list_excluded(self, ctx):
        """List excluded voice channels."""
        excluded = await self.config.guild(ctx.guild).excluded_voice_ids()
        if not excluded:
            await ctx.send("✅ No voice channels are currently excluded.")
            return
        names = []
        for cid in excluded:
            ch = ctx.guild.get_channel(cid)
            names.append(ch.name if ch else f"Unknown Channel ({cid})")
        await ctx.send("🚫 Excluded channels:\n" + ", ".join(names))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Only track joins and leaves
        if member.bot or before.channel == after.channel:
            return

        guild = member.guild
        text_channel_id = await self.config.guild(guild).text_channel_id()
        excluded = await self.config.guild(guild).excluded_voice_ids()
        text_channel = guild.get_channel(text_channel_id)

        # User joined a voice channel
        if after.channel and after.channel.id not in excluded:
            if text_channel:
                await text_channel.send(f"🔔 {member.mention} joined **{after.channel.name}**.")

        # User left a voice channel
        if before.channel and before.channel.id not in excluded:
            # Check if the channel is now empty (no non-bot members)
            if len([m for m in before.channel.members if not m.bot]) == 0:
                if text_channel:
                    await text_channel.send(f"🔕 Voice stopped in **{before.channel.name}** (channel is now empty).")
