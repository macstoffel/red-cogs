import discord
from redbot.core import commands, Config
from discord.ext import tasks
from datetime import datetime

class TimeMatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123456789)
        default_guild = {"channel_id": None}
        self.config.register_guild(**default_guild)
        self.time_check_loop.start()
        self.last_sent_minute = None  # Track last sent minute

    def cog_unload(self):
        self.time_check_loop.cancel()

    @commands.group()
    @commands.admin()
    async def timematchcog(self, ctx):
        """TimeMatchCog configuration commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @timematchcog.command()
    async def settimematchchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for time match notifications."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"✅ Time match channel set to {channel.mention}.")

    @tasks.loop(minutes=1)
    async def time_check_loop(self):
        now = datetime.now()
        hour = now.strftime("%H")
        minute = now.strftime("%M")

        for guild in self.bot.guilds:
            channel_id = await self.config.guild(guild).channel_id()
            if not channel_id:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            if hour == minute and self.last_sent_minute != minute:
                await channel.send(f"```diff\n- **HET IS {hour}:{minute} ... TIK DE GROND!**\n```")
                self.last_sent_minute = minute
            elif hour != minute:
                self.last_sent_minute = None  # Reset for next match

    @time_check_loop.before_loop
    async def before_time_check(self):
        await self.bot.wait_until_ready()