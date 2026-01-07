import discord
import random
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta

from redbot.core import commands, Config
from redbot.core.bot import Red

PURPLE = discord.Color.purple()
TASK_FILE = Path(__file__).parent / "tasks.json"


# =========================
# BUTTON VIEWS
# =========================
class RouletteView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="🎯 Mannen taak", style=discord.ButtonStyle.primary)
    async def male(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.request_task(interaction, "male")

    @discord.ui.button(label="🎯 Vrouwen taak", style=discord.ButtonStyle.primary)
    async def female(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.request_task(interaction, "female")


class ProofReviewView(discord.ui.View):
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label="✅ Goedkeuren", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.cog.can_approve(interaction.user):
            return await interaction.response.send_message(
                "❌ Je mag geen bewijs goedkeuren.", ephemeral=True
            )
        await self.cog.approve_proof(interaction, self.user_id)

    @discord.ui.button(label="❌ Afkeuren", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.cog.can_approve(interaction.user):
            return await interaction.response.send_message(
                "❌ Je mag geen bewijs afkeuren.", ephemeral=True
            )
        await self.cog.deny_proof(interaction, self.user_id)


# =========================
# MAIN COG
# =========================
class Roulette(commands.Cog):
    """Takenroulette met JSON-taken, buttons, proof, approvals en logging"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=7788990011)

        # Guild config
        self.config.register_guild(
            button_channel=None,
            proof_channel=None,
            log_channel=None,
            cooldown_hours=24,
            approve_required=True,
            approve_role=None,
            stats={}
        )

        # User config
        self.config.register_user(
            active_task={},       # lege dict i.p.v. None
            last_request=None
        )

        # Load tasks from JSON
        self.tasks = self.load_tasks()

    # =========================
    # TASKS JSON HANDLING
    # =========================
    def load_tasks(self):
        if TASK_FILE.exists():
            with open(TASK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"male": [], "female": []}

    def save_tasks(self):
        with open(TASK_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=4, ensure_ascii=False)

    # =========================
    # HELPERS
    # =========================
    async def log(self, guild, title, description):
        channel_id = await self.config.guild(guild).log_channel()
        if not channel_id:
            return
        channel = guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(title=title, description=description, color=PURPLE)
            await channel.send(embed=embed)

    async def can_approve(self, member: discord.Member):
        if member.guild_permissions.administrator:
            return True
        role_id = await self.config.guild(member.guild).approve_role()
        if not role_id:
            return False
        role = member.guild.get_role(role_id)
        return role in member.roles if role else False

    # =========================
    # TASK REQUEST
    # =========================
    async def request_task(self, interaction: discord.Interaction, gender: str):
        user = interaction.user
        guild = interaction.guild
        now = datetime.utcnow()

        cooldown = await self.config.guild(guild).cooldown_hours()
        user_data = await self.config.user(user).all()

        active_task = user_data.get("active_task", {})
        if active_task:  # dict niet leeg → actieve taak
            return await interaction.response.send_message(
                "❌ Je hebt nog een openstaande taak zonder bewijs.",
                ephemeral=True
            )

        last_request = user_data.get("last_request")
        if last_request:
            last = datetime.fromisoformat(last_request)
            if now < last + timedelta(hours=cooldown):
                msg = await interaction.response.send_message(
                    f"⏳ Geen bewijs? Dan kun je maar **1 taak per {cooldown} uur** aanvragen.",
                    ephemeral=True
                )
                await asyncio.sleep(20)
                await interaction.delete_original_response()
                return

        if not self.tasks.get(gender):
            return await interaction.response.send_message(
                "❌ Geen taken beschikbaar.",
                ephemeral=True
            )

        task = random.choice(self.tasks[gender])

        await self.config.user(user).active_task.set({
            "task": task,
            "gender": gender,
            "time": now.isoformat()
        })
        await self.config.user(user).last_request.set(now.isoformat())

        # Update stats
        stats = await self.config.guild(guild).stats()
        uid = str(user.id)
        stats.setdefault(uid, {"male": 0, "female": 0})
        stats[uid][gender] += 1
        await self.config.guild(guild).stats.set(stats)

        proof_channel = guild.get_channel(await self.config.guild(guild).proof_channel())

        embed = discord.Embed(
            title="📸 Bewijs vereist",
            description=(
                f"**Gebruiker:** {user.mention}\n"
                f"**Categorie:** {gender}\n"
                f"**Taak:** {task}\n\n"
                f"Plaats hier je bewijs.\n"
                f"❗ Geen bewijs = 1 taak per {cooldown} uur"
            ),
            color=PURPLE
        )

        await proof_channel.send(embed=embed)

        await self.log(
            guild,
            "🎯 Taak aangevraagd",
            f"{user.mention}\nCategorie: {gender}\nTaak: {task}"
        )

        await interaction.response.send_message(
            f"✅ Taak geplaatst in {proof_channel.mention}", ephemeral=True
        )

    # =========================
    # PROOF HANDLING
    # =========================
    async def approve_proof(self, interaction, user_id: int):
        user = interaction.guild.get_member(user_id)
        await self.config.user(user).active_task.set({})
        await self.config.user(user).last_request.set(None)

        await self.log(
            interaction.guild,
            "✅ Bewijs goedgekeurd",
            f"{interaction.user.mention} keurde bewijs goed van {user.mention}"
        )

        await interaction.response.send_message(
            f"✅ Bewijs goedgekeurd voor {user.mention}"
        )

    async def deny_proof(self, interaction, user_id: int):
        await self.log(
            interaction.guild,
            "❌ Bewijs afgekeurd",
            f"{interaction.user.mention} keurde bewijs af"
        )

        await interaction.response.send_message(
            "❌ Bewijs afgekeurd. Cooldown blijft actief."
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        proof_channel_id = await self.config.guild(message.guild).proof_channel()
        if not proof_channel_id or message.channel.id != proof_channel_id:
            return

        if not (message.attachments or "http" in message.content):
            return

        active = await self.config.user(message.author).active_task()
        if not active:
            return

        approve_required = await self.config.guild(message.guild).approve_required()

        if not approve_required:
            await self.config.user(message.author).active_task.set({})
            await self.config.user(message.author).last_request.set(None)

            await self.log(
                message.guild,
                "✅ Bewijs automatisch goedgekeurd",
                f"{message.author.mention}"
            )
            return

        await message.channel.send(
            embed=discord.Embed(
                title="🛂 Bewijs ontvangen",
                description=f"{message.author.mention} heeft bewijs geleverd.",
                color=PURPLE
            ),
            view=ProofReviewView(self, message.author.id)
        )

    # =========================
    # COMMANDS
    # =========================
    @commands.group()
    async def roulette(self, ctx):
        """Roulette hoofdcommando"""

    # --- setup
    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def setup(self, ctx, button_channel: discord.TextChannel, proof_channel: discord.TextChannel):
        await self.config.guild(ctx.guild).button_channel.set(button_channel.id)
        await self.config.guild(ctx.guild).proof_channel.set(proof_channel.id)

        await button_channel.send(
            embed=discord.Embed(
                title="🎰 Roulette",
                description="Klik op een knop om een taak te krijgen.",
                color=PURPLE
            ),
            view=RouletteView(self)
        )

        await ctx.send("✅ Roulette ingesteld.")

    # --- logchannel
    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def logchannel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send("✅ Logkanaal ingesteld.")

    # --- approve aan/uit
    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def approve(self, ctx, mode: str):
        if mode.lower() not in ("on", "off"):
            return await ctx.send("Gebruik `on` of `off`.")
        await self.config.guild(ctx.guild).approve_required.set(mode.lower() == "on")
        await ctx.send(f"✅ Approve {'ingeschakeld' if mode == 'on' else 'uitgeschakeld'}.")

    # --- approverole
    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def approverole(self, ctx, role: str):
        """Stel in welke rol bewijs mag goedkeuren of verwijder met 'remove'."""
        if role.lower() == "remove":
            await self.config.guild(ctx.guild).approve_role.set(None)
        return await ctx.send("✅ Approverol verwijderd.")
    
    # Probeer rol te converteren
    role_obj = discord.utils.get(ctx.guild.roles, name=role) or discord.utils.get(ctx.guild.roles, id=int(role))
    if not role_obj:
        return await ctx.send("❌ Rol niet gevonden. Gebruik naam of ID.")

        await self.config.guild(ctx.guild).approve_role.set(role_obj.id)
        await ctx.send(f"✅ {role_obj.name} mag nu bewijs goedkeuren.")
    # --- addtask
    @roulette.command()
    async def addtask(self, ctx, gender: str, *, task: str):
        gender = gender.lower()
        if gender not in ("male", "female"):
            return await ctx.send("Gebruik `male` of `female`.")
        self.tasks[gender].append(task)
        self.save_tasks()
        await ctx.send(f"✅ Taak toegevoegd aan {gender}.")

    # --- removetask
    @roulette.command()
    async def removetask(self, ctx, gender: str, index: int):
        gender = gender.lower()
        try:
            removed = self.tasks[gender].pop(index)
            self.save_tasks()
            await ctx.send(f"🗑️ Verwijderd: {removed}")
        except Exception:
            await ctx.send("❌ Ongeldige index of categorie.")

    # --- tasks
    @roulette.command()
    async def tasks(self, ctx):
        embed = discord.Embed(title="📋 Takenlijst", color=PURPLE)
        embed.add_field(name="Mannen", value="\n".join(self.tasks["male"]) or "Geen")
        embed.add_field(name="Vrouwen", value="\n".join(self.tasks["female"]) or "Geen")
        await ctx.send(embed=embed)

    # --- cooldown
    @roulette.command()
    async def cooldown(self, ctx, hours: int):
        await self.config.guild(ctx.guild).cooldown_hours.set(hours)
        await ctx.send(f"⏱️ Cooldown ingesteld op {hours} uur.")

    # --- stats
    @roulette.command()
    async def stats(self, ctx):
        stats = await self.config.guild(ctx.guild).stats()
        if not stats:
            return await ctx.send("❌ Geen data.")
        desc = ""
        for uid, data in stats.items():
            member = ctx.guild.get_member(int(uid))
            if member:
                desc += f"**{member.display_name}** → M:{data['male']} V:{data['female']}\n"
        await ctx.send(embed=discord.Embed(title="📊 Roulette Statistieken", description=desc, color=PURPLE))

    # --- settings
    @roulette.command()
    async def settings(self, ctx):
        g = self.config.guild(ctx.guild)
        embed = discord.Embed(title="⚙️ Instellingen", color=PURPLE)
        embed.add_field(name="Knoppenkanaal", value=f"<#{await g.button_channel()}>")
        embed.add_field(name="Bewijskanaal", value=f"<#{await g.proof_channel()}>")
        embed.add_field(name="Logkanaal", value=f"<#{await g.log_channel()}>" if await g.log_channel() else "Niet ingesteld")
        embed.add_field(name="Cooldown (uur)", value=await g.cooldown_hours())
        embed.add_field(name="Approve vereist", value=await g.approve_required())
        embed.add_field(
            name="Approve rol",
            value=f"<@&{await g.approve_role()}>" if await g.approve_role() else "Niet ingesteld"
        )
        await ctx.send(embed=embed)
