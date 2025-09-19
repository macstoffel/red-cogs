import discord
from redbot.core import commands, Config
from datetime import datetime, timedelta


class InactiveKicker(commands.Cog):
    """Toon of kick inactieve leden gebaseerd op laatste activiteit."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_member = {"last_active": None}
        self.config.register_member(**default_member)

    # ------------------------
    # Activiteit tracken
    # ------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild and not message.author.bot:
            await self.config.member(message.author).last_active.set(datetime.utcnow().timestamp())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.guild and not member.bot:
            if after.channel is not None:  # join of switch naar voice
                await self.config.member(member).last_active.set(datetime.utcnow().timestamp())

    # ------------------------
    # Command
    # ------------------------
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def inactive(self, ctx, role: discord.Role, days: int, action: str = "show"):
        """
        Controleer of kick inactieve gebruikers.
        role: De rol om te filteren.
        days: Aantal dagen inactief.
        action: 'show' of 'kick'.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        inactieve = []

        for member in role.members:
            ts = await self.config.member(member).last_active()
            print(f"{member.display_name}: last_active={ts}")
            if ts:
                laatste = datetime.utcfromtimestamp(float(ts))
            else:
                laatste = (member.joined_at.replace(tzinfo=None) if member.joined_at else datetime.utcnow())  # fallback

            if laatste < cutoff:
                inactieve.append(member)

        if not inactieve:
            return await ctx.send("Geen inactieve gebruikers gevonden.")

        if action.lower() == "show":
            lijst = "\n".join([f"{m} (ID: {m.id})" for m in inactieve])
            await ctx.send(f"Inactieve gebruikers (>{days} dagen):\n{lijst[:1900]}")
        elif action.lower() == "kick":
            gekickt = 0
            for m in inactieve:
                try:
                    await m.kick(reason=f"Inactief voor {days}+ dagen")
                    gekickt += 1
                except Exception as e:
                    await ctx.send(f"Kon {m} niet kicken: {e}")
            await ctx.send(f"{gekickt} gebruiker(s) gekickt.")
        else:
            await ctx.send("Ongeldige actie. Gebruik 'show' of 'kick'.")

    @commands.command()
    @commands.is_owner()
    async def import_seen(self, ctx):
        """
        Importeer laatste activiteit uit AAA3A's Seen cog naar InactiveKicker.
        """
        seen_config = Config.get_conf("Seen", identifier=205192943327321000143939875896557571750)
        members_data = await seen_config.all_members()
        guild_id = str(ctx.guild.id)
        count = 0
        if guild_id not in members_data:
            await ctx.send("Geen Seen-data gevonden voor deze server.")
            return
        guild_members = members_data[guild_id]
        global_data = await seen_config.all()
        for member in ctx.guild.members:
            mdata = guild_members.get(str(member.id), {})
            custom_id = mdata.get("message")
            if custom_id:
                message_data = global_data.get("message", {}).get(custom_id)
                if message_data and "seen" in message_data:
                    await self.config.member(member).last_active.set(float(message_data["seen"]))
                    count += 1
        await ctx.send(f"Geïmporteerd: laatste activiteit voor {count} leden uit Seen.")
