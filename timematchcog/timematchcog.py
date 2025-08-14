import discord
from redbot.core import commands, Config
from discord.ext import tasks
from datetime import datetime

class TimeMatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123456789)
        default_guild = {"channel_id": None, "role_id": None, "last_double_time": None, "last_minute": None}
        default_member = {"score": 0}
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)
        self.last_sent_minute = None
        self.last_reported_minute = None
        self.time_check_loop.start()

    def cog_unload(self):
        self.time_check_loop.cancel()

    @commands.group(name="timematchcog")
    @commands.admin()
    async def timematchcog(self, ctx):
        """TimeMatchCog configuratie commando's."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @timematchcog.command()
    async def settimematchchannel(self, ctx, channel: discord.TextChannel):
        """Stel het kanaal in voor tijdmeldingen."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"✅ Tijdmeldingen kanaal ingesteld op {channel.mention}.")

    @timematchcog.command()
    async def settimematchrole(self, ctx, role: discord.Role):
        """Stel de rol in die gepingd wordt bij dubbele tijd."""
        await self.config.guild(ctx.guild).role_id.set(role.id)
        await ctx.send(f"✅ Tijdmeldingen rol ingesteld op {role.mention}.")

    @timematchcog.command()
    async def status(self, ctx):
        """Toon huidige instellingen."""
        channel_id = await self.config.guild(ctx.guild).channel_id()
        role_id = await self.config.guild(ctx.guild).role_id()
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        role = ctx.guild.get_role(role_id) if role_id else None
        msg = (
            f"**TimeMatchCog Instellingen:**\n"
            f"Kanaal: {channel.mention if channel else 'Niet ingesteld'}\n"
            f"Rol: {role.mention if role else 'Niet ingesteld'}"
        )
        await ctx.send(msg)

    @timematchcog.command()
    async def score(self, ctx, member: discord.Member = None):
        """Toon de score van een gebruiker (of jezelf)."""
        member = member or ctx.author
        score = await self.config.member(member).score()
        await ctx.send(f"{member.display_name} heeft {score} punten!")

    @timematchcog.command()
    async def top(self, ctx):
        """Toon de top 10 scores."""
        members = ctx.guild.members
        scores = []
        for member in members:
            score = await self.config.member(member).score()
            if score > 0:
                scores.append((member.display_name, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        msg = "**Top 10 Kus de grond scores:**\n"
        for i, (name, score) in enumerate(scores[:10], 1):
            msg += f"{i}. {name}: {score}\n"
        await ctx.send(msg if scores else "Nog geen scores!")

    @tasks.loop(seconds=5)
    async def time_check_loop(self):
        now = datetime.now()
        hour = now.strftime("%H")
        minute = now.strftime("%M")
        current_time = f"{hour}:{minute}"

        for guild in self.bot.guilds:
            channel_id = await self.config.guild(guild).channel_id()
            role_id = await self.config.guild(guild).role_id()
            if not channel_id:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            last_double_time = await self.config.guild(guild).last_double_time()
            last_minute = await self.config.guild(guild).last_minute()

            role_mention = f"<@&{role_id}>" if role_id else ""
            # Directe melding bij nieuwe dubbele tijd
            if hour == minute and last_double_time != current_time:
                await self.config.guild(guild).last_double_time.set(current_time)
                await self.config.guild(guild).last_minute.set(minute)
                await channel.send(f"{role_mention} **Het is {hour}:{minute} ... Kus de grond?**")
            # Na afloop van de minuut, score tonen (eenmalig)
            elif hour != minute and last_double_time is not None:
                if last_minute is not None and last_minute != minute:
                    await self.show_top_scores(channel)
                    await self.config.guild(guild).last_double_time.set(None)
                    await self.config.guild(guild).last_minute.set(None)

    async def show_top_scores(self, channel):
        members = channel.guild.members
        scores = []
        for member in members:
            score = await self.config.member(member).score()
            if score > 0:
                scores.append((member.display_name, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        msg = "**Top 10 Kus de grond scores:**\n"
        for i, (name, score) in enumerate(scores[:10], 1):
            msg += f"{i}. {name}: {score}\n"
        await channel.send(msg if scores else "Nog geen scores!")

    @time_check_loop.before_loop
    async def before_time_check(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        guild = message.guild
        channel_id = await self.config.guild(guild).channel_id()
        if not channel_id or message.channel.id != channel_id:
            return

        last_double_time = await self.config.guild(guild).last_double_time()
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        content = message.content.lower()

        score = await self.config.member(message.author).score()
        # Alleen reageren op "kus"
        if "kus" in content:
            if last_double_time == current_time:
                await self.config.member(message.author).score.set(score + 1)
                await message.channel.send(f"{message.author.mention} krijgt een punt! Totaal: {score + 1}")
            else:
                new_score = max(0, score - 1)
                await self.config.member(message.author).score.set(new_score)
                await message.channel.send(f"{message.author.mention} verliest een punt! Totaal: {new_score}")

    def cog_load(self):
        self.time_check_loop.start()

    def cog_unload(self):
        self.time_check_loop.cancel()