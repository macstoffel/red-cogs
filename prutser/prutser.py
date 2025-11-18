import discord
from redbot.core import commands, Config
import asyncio
import datetime

class Prutser(commands.Cog):
    """Een cog die tijdelijk de rol 'prutser' toekent aan een gebruiker."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_member = {
            "assigned_at": None,
            "duration": 3600
        }
        self.config.register_member(**default_member)
        default_guild = {
            "default_duration": 3600,
            "log_channel": None
        }
        self.config.register_guild(**default_guild)

    async def log_action(self, guild, message):
        channel_id = await self.config.guild(guild).log_channel()
        if not channel_id:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            try:
                channel = await guild.fetch_channel(channel_id)
            except Exception:
                return
        if channel and channel.permissions_for(guild.me).send_messages:
            try:
                await channel.send(message)
            except Exception:
                pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def prutserlog(self, ctx, channel: discord.TextChannel):
        """Stel het logkanaal in voor prutser-acties."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Logkanaal ingesteld op {channel.mention}.")

    @commands.command()
    async def prutser_settings(self, ctx):
        """Toon de huidige prutser-instellingen."""
        log_channel_id = await self.config.guild(ctx.guild).log_channel()
        duration = await self.config.guild(ctx.guild).default_duration()
        log_channel = ctx.guild.get_channel(log_channel_id) if log_channel_id else None
        log_channel_str = log_channel.mention if log_channel else "Niet ingesteld"
        await ctx.send(
            f"**Prutser instellingen:**\n"
            f"Logkanaal: {log_channel_str}\n"
            f"Standaard duur: {duration} seconden"
        )

    @commands.command()
    async def prutser(self, ctx, *args):
        """Beheer de prutser-rol. Opties: @user | status | clear @user | duration <tijd> | tijd @user"""
        if len(args) == 0:
            await ctx.send(
                "**Prutser Cog Help**\n"
                "`$prutser @user` – wijs iemand tijdelijk de prutser-rol toe\n"
                "`$prutser clear @user` – verwijder prutser-rol direct\n"
                "`$prutser status` – laat zien wie nu prutser is\n"
                "`$prutser duration 10m` – pas de standaardtijd aan\n"
                "`$prutserlog #kanaal` – stel het logkanaal in\n"
                "`$prutser_settings` – toon de huidige instellingen\n\n"
                "Gemaakt door MacStoffel"
            )
            return

        if args[0].lower() == "status":
            await self.status(ctx)
            await self.log_action(ctx.guild, f":mag: {ctx.author.display_name} heeft `$prutser status` uitgevoerd.")
        elif args[0].lower() == "clear" and len(args) > 1:
            member = await commands.MemberConverter().convert(ctx, args[1])
            await self.clear_prutser(ctx, member)
            await self.log_action(ctx.guild, f":wastebasket: {ctx.author.display_name} heeft de prutser-rol verwijderd van {member.display_name}.")
        elif args[0].lower() == "duration" and len(args) > 1:
            await self.set_duration(ctx, args[1])
            await self.log_action(ctx.guild, f":clock1: {ctx.author.display_name} heeft de standaard prutser-duur aangepast naar {args[1]}.")
        elif args[0].lower() == "tijd" and len(args) > 1:
            member = await commands.MemberConverter().convert(ctx, args[1])
            await self.show_time_left(ctx, member)
            await self.log_action(ctx.guild, f":hourglass: {ctx.author.display_name} heeft de resterende tijd van {member.display_name} opgevraagd.")
        else:
            try:
                member = await commands.MemberConverter().convert(ctx, args[0])
                await self.assign_prutser_role(ctx, member, ctx.author)
            except commands.BadArgument:
                await ctx.send("Kon de gebruiker niet vinden.")

    async def assign_prutser_role(self, ctx, member, moderator=None):
        prutser_role = discord.utils.get(ctx.guild.roles, name="prutser")
        if not prutser_role:
            await ctx.send("De rol 'prutser' bestaat niet.")
            return

        if prutser_role in member.roles:
            await ctx.send(f"{member.display_name} is al een prutser.")
            return

        await member.add_roles(prutser_role)
        await ctx.send(f"{member.display_name} is nu een prutser.")
        mod_name = moderator.display_name if moderator else ctx.author.display_name
        await self.log_action(ctx.guild, f":warning: {member.display_name} is nu een prutser (toegevoegd door {mod_name}).")

        duration = await self.config.member(member).duration()
        if not duration or duration == 3600:
            duration = await self.config.guild(ctx.guild).default_duration()
            if not duration:
                duration = 3600

        assigned_at = datetime.datetime.utcnow().timestamp()
        await self.config.member(member).assigned_at.set(assigned_at)
        await self.config.member(member).duration.set(duration)

        await asyncio.sleep(duration)

        if prutser_role in member.roles:
            try:
                await member.remove_roles(prutser_role)
                await self.config.member(member).clear()
                await ctx.send(f"{member.display_name} is geen prutser meer.")
                await self.log_action(ctx.guild, f":white_check_mark: {member.display_name} is geen prutser meer (timer verlopen).")
            except discord.Forbidden:
                await ctx.send(f"Geen toestemming om de prutser-rol van {member.display_name} te verwijderen.")
                await self.log_action(ctx.guild, f":x: Kon de prutser-rol niet verwijderen van {member.display_name} (geen toestemming).")
            await self.config.member(member).clear()

    async def clear_prutser(self, ctx, member):
        prutser_role = discord.utils.get(ctx.guild.roles, name="prutser")
        if prutser_role in member.roles:
            await member.remove_roles(prutser_role)
            await self.config.member(member).clear()
            await ctx.send(f"{member.display_name} is geen prutser meer.")
            await self.log_action(ctx.guild, f":wastebasket: {member.display_name} is geen prutser meer (handmatig verwijderd).")
        else:
            await ctx.send(f"{member.display_name} is geen prutser.")

    async def status(self, ctx):
        prutser_role = discord.utils.get(ctx.guild.roles, name="prutser")
        if not prutser_role:
            await ctx.send("De rol 'prutser' bestaat niet.")
            return

        prutsers = [m for m in ctx.guild.members if prutser_role in m.roles]
        if not prutsers:
            await ctx.send("Er zijn momenteel geen prutsers.")
            return

        lines = []
        now = datetime.datetime.utcnow().timestamp()
        for member in prutsers:
            assigned_at = await self.config.member(member).assigned_at()
            duration = await self.config.member(member).duration()
            if assigned_at and duration:
                seconds_left = int((assigned_at + duration) - now)
                if seconds_left > 0:
                    minutes, seconds = divmod(seconds_left, 60)
                    tijd_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                else:
                    tijd_str = "verlopen"
            else:
                tijd_str = "onbekend"
            lines.append(f"**{member.display_name}**: {tijd_str} over")

        await ctx.send("Huidige prutsers:\n" + "\n".join(lines))

    async def set_duration(self, ctx, tijd):
        tijd = tijd.lower()
        multiplier = 1
        if tijd.endswith("m"):
            multiplier = 60
            tijd = tijd[:-1]
        elif tijd.endswith("h"):
            multiplier = 3600
            tijd = tijd[:-1]
        try:
            seconds = int(tijd) * multiplier
            await self.config.guild(ctx.guild).default_duration.set(seconds)
            await ctx.send(f"Standaardduur ingesteld op {seconds} seconden.")
        except ValueError:
            await ctx.send("Ongeldige tijd. Gebruik bijvoorbeeld: 10m of 1h.")

    async def show_time_left(self, ctx, member):
        prutser_role = discord.utils.get(ctx.guild.roles, name="prutser")
        if prutser_role not in member.roles:
            await ctx.send(f"{member.display_name} is geen prutser.")
            return

        assigned_at = await self.config.member(member).assigned_at()
        duration = await self.config.member(member).duration()

        if not assigned_at or not duration:
            await ctx.send(f"Geen timergegevens gevonden voor {member.display_name}.")
            return

        now = datetime.datetime.utcnow().timestamp()
        seconds_left = int((assigned_at + duration) - now)

        if seconds_left <= 0:
            await ctx.send(f"De prutsertijd van {member.display_name} is eigenlijk al voorbij.")
            return

        minutes, seconds = divmod(seconds_left, 60)
        tijd_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        await ctx.send(f"{member.display_name} is nog {tijd_str} prutser.")

    async def on_member_update(self, before, after):
        if not hasattr(after, "guild"):
            return

        prutser_role = discord.utils.get(after.guild.roles, name="prutser")
        if not prutser_role:
            return

        if prutser_role not in before.roles and prutser_role in after.roles:
            assigned_at = await self.config.member(after).assigned_at()
            if not assigned_at:
                duration = await self.config.guild(after.guild).default_duration()
                if not duration:
                    duration = 3600
                now = datetime.datetime.utcnow().timestamp()
                await self.config.member(after).assigned_at.set(now)
                await self.config.member(after).duration.set(duration)
                await self.log_action(after.guild, f":warning: {after.display_name} heeft de prutser-rol gekregen. Timer gestart voor {duration} seconden. De volgende gebruiker begint met 1")
                asyncio.create_task(self._remove_prutser_later(after, prutser_role, duration))

    async def _remove_prutser_later(self, member, prutser_role, duration):
        await asyncio.sleep(duration)
        if prutser_role in member.roles:
            try:
                await member.remove_roles(prutser_role)
                await self.log_action(member.guild, f":white_check_mark: {member.display_name} is geen prutser meer (timer verlopen).")
            except discord.Forbidden:
                await self.log_action(member.guild, f":x: Kon de prutser-rol niet verwijderen van {member.display_name} (geen toestemming, handmatig toegevoegd).")
            await self.config.member(member).clear()

    def cog_load(self):
        self.bot.add_listener(self.on_member_update, "on_member_update")

    def cog_unload(self):
        self.bot.remove_listener(self.on_member_update, "on_member_update")

async def setup(bot):
    await bot.add_cog(Prutser(bot))