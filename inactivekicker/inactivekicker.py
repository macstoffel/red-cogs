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
            if ts:
                laatste = datetime.utcfromtimestamp(ts)
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
