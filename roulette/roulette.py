import asyncio
import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

PURPLE = discord.Color.purple()
TASK_FILE = Path(__file__).parent / "tasks.json"
DEFAULT_TASKS = {"male": [], "female": []}
GENDERS = ("male", "female")


def parse_dt(value):
    """ISO-string naar aware datetime (UTC). None als het ontbreekt of ongeldig is."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# =========================
# BUTTON VIEWS
# =========================
class RouletteView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="🎯 Mannen taak",
        style=discord.ButtonStyle.primary,
        custom_id="roulette:task:male",
    )
    async def male(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.request_task(interaction, "male")

    @discord.ui.button(
        label="🎯 Vrouwen taak",
        style=discord.ButtonStyle.primary,
        custom_id="roulette:task:female",
    )
    async def female(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.request_task(interaction, "female")


class ProofReviewView(discord.ui.View):
    """Vaste custom_id's, zodat de knoppen een botrestart overleven."""

    def __init__(self, cog, disabled: bool = False):
        super().__init__(timeout=None)
        self.cog = cog
        if disabled:
            for item in self.children:
                item.disabled = True

    @discord.ui.button(
        label="✅ Goedkeuren",
        style=discord.ButtonStyle.success,
        custom_id="roulette:proof:approve",
    )
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_proof_review(interaction, approved=True)

    @discord.ui.button(
        label="❌ Afkeuren",
        style=discord.ButtonStyle.danger,
        custom_id="roulette:proof:deny",
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_proof_review(interaction, approved=False)


# =========================
# MAIN COG
# =========================
class Roulette(commands.Cog):
    """Takenroulette met JSON-taken, buttons, proof, approvals en logging"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=7788990011)

        self.config.register_guild(
            button_channel=None,
            proof_channel=None,
            log_channel=None,
            cooldown_hours=24,
            approve_required=True,
            approve_role=None,
            stats={},
            reviews={},
        )
        self.config.register_user(
            active_task={},
            last_request=None,
        )

        self.tasks = self.load_tasks()
        self._locks = {}

    async def cog_load(self):
        # Zonder add_view werken de knoppen niet meer na een restart.
        self._task_view = RouletteView(self)
        self._proof_view = ProofReviewView(self)
        self.bot.add_view(self._task_view)
        self.bot.add_view(self._proof_view)

    async def cog_unload(self):
        for attr in ("_task_view", "_proof_view"):
            view = getattr(self, attr, None)
            if view is not None:
                view.stop()

    # =========================
    # TASKS JSON HANDLING
    # =========================
    def load_tasks(self):
        empty = {gender: [] for gender in GENDERS}
        if not TASK_FILE.exists():
            return empty
        try:
            with open(TASK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[roulette] tasks.json onleesbaar, lege lijsten gebruikt: {exc}")
            return empty
        if not isinstance(data, dict):
            print("[roulette] tasks.json heeft geen object als root, lege lijsten gebruikt.")
            return empty
        return {
            gender: [task for task in data.get(gender, []) if isinstance(task, str)]
            for gender in GENDERS
        }

    def save_tasks(self):
        tmp = TASK_FILE.with_name(TASK_FILE.name + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, TASK_FILE)
        except OSError as exc:
            print(f"[roulette] kon tasks.json niet opslaan: {exc}")

    # =========================
    # HELPERS
    # =========================
    @staticmethod
    def fmt_delta(delta: timedelta) -> str:
        total = max(0, int(delta.total_seconds()))
        hours, rest = divmod(total, 3600)
        minutes = rest // 60
        return f"{hours}u {minutes}m" if hours else f"{minutes}m"

    def lock_for(self, key: str) -> asyncio.Lock:
        return self._locks.setdefault(key, asyncio.Lock())

    @staticmethod
    def review_user_id(entry):
        """Een reviews-entry is een dict; int wordt nog geaccepteerd voor oude data."""
        if isinstance(entry, dict):
            return entry.get("user_id")
        return entry if isinstance(entry, int) else None

    async def log(self, guild, title: str, description: str):
        if guild is None:
            return
        channel_id = await self.config.guild(guild).log_channel()
        channel = guild.get_channel(channel_id) if channel_id else None
        if channel is None:
            return
        try:
            await channel.send(
                embed=discord.Embed(title=title, description=description, color=PURPLE)
            )
        except discord.HTTPException:
            pass

    async def can_approve(self, member) -> bool:
        if not isinstance(member, discord.Member):
            return False
        if member.guild_permissions.administrator:
            return True
        role_id = await self.config.guild(member.guild).approve_role()
        if not role_id:
            return False
        role = member.guild.get_role(role_id)
        return role is not None and role in member.roles

    async def review_line(self, guild) -> str:
        """Regel onder het taakbericht die vertelt wie het bewijs beoordeelt."""
        conf_guild = self.config.guild(guild)
        if not await conf_guild.approve_required():
            return "✅ Je bewijs wordt automatisch goedgekeurd.\n"
        role_id = await conf_guild.approve_role()
        role = guild.get_role(role_id) if role_id else None
        if role is not None:
            return f"🛡️ Je bewijs wordt beoordeeld door **{role.name}**.\n"
        return "🛡️ Je bewijs wordt beoordeeld door een moderator.\n"

    @staticmethod
    async def nudge_reply(message: discord.Message):
        """Zeg het één keer als iemand bewijs plaatst zonder reply op het taakbericht."""
        try:
            await message.reply(
                "❗ Dit telt niet als bewijs. **Reageer op het taakbericht** met je "
                "tekst, foto of video.",
                mention_author=True,
                delete_after=15,
            )
        except discord.HTTPException:
            pass

    # =========================
    # TASK REQUEST
    # =========================
    async def request_task(self, interaction: discord.Interaction, gender: str):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "❌ Dit werkt alleen binnen een server.", ephemeral=True
            )

        guild = interaction.guild
        user = interaction.user

        async with self.lock_for(f"task:{user.id}"):
            now = datetime.now(timezone.utc)
            conf_guild = self.config.guild(guild)
            conf_user = self.config.user(user)

            cooldown = await conf_guild.cooldown_hours()
            user_data = await conf_user.all()
            active = user_data.get("active_task") or {}

            # Regel: taak open = geen nieuwe taak, tot er bewijs is of de uren om zijn.
            deadline = None
            if active:
                started = parse_dt(active.get("time"))
                if started is not None:
                    deadline = started + timedelta(hours=cooldown)
                if deadline is None or now >= deadline:
                    await conf_user.active_task.set({})
                    active = {}
                    deadline = None

            if active:
                remaining = self.fmt_delta(deadline - now) if deadline else "onbekend"
                return await interaction.response.send_message(
                    f"❌ Je hebt nog een openstaande taak zonder bewijs. Nog {remaining}.",
                    ephemeral=True,
                )

            last = parse_dt(user_data.get("last_request"))
            if last and now < last + timedelta(hours=cooldown):
                remaining = self.fmt_delta(last + timedelta(hours=cooldown) - now)
                await interaction.response.send_message(
                    f"⏳ Je bewijs is afgekeurd. Je kunt over {remaining} weer een "
                    f"taak aanvragen.",
                    ephemeral=True,
                )
                try:
                    message = await interaction.original_response()
                    await message.delete(delay=20)
                except discord.HTTPException:
                    pass
                return

            pool = self.tasks.get(gender) or []
            if not pool:
                return await interaction.response.send_message(
                    "❌ Geen taken beschikbaar.", ephemeral=True
                )

            proof_channel_id = await conf_guild.proof_channel()
            proof_channel = guild.get_channel(proof_channel_id) if proof_channel_id else None
            if proof_channel is None:
                return await interaction.response.send_message(
                    "❌ Bewijskanaal niet ingesteld of verwijderd. "
                    "Vraag een admin om `roulette setup`.",
                    ephemeral=True,
                )

            task = random.choice(pool)
            review_line = await self.review_line(guild)

            # Eerst het bewijsbericht plaatsen; pas daarna state aanpassen.
            try:
                proof_message = await proof_channel.send(
                    embed=discord.Embed(
                        title="📸 Bewijs vereist",
                        description=(
                            f"**Gebruiker:** {user.mention}\n"
                            f"**Categorie:** {gender}\n"
                            f"**Taak:** {task}\n\n"
                            f"📎 **Lever je bewijs als reply op dít bericht** — "
                            f"tekst, foto of video.\n"
                            f"{review_line}"
                            f"❗ Lever je geen bewijs, dan kun je {cooldown} uur lang "
                            f"geen nieuwe taak aanvragen."
                        ),
                        color=PURPLE,
                    )
                )
            except discord.HTTPException:
                return await interaction.response.send_message(
                    "❌ Kon geen bericht plaatsen in het bewijskanaal. "
                    "Controleer de rechten.",
                    ephemeral=True,
                )

            await conf_user.active_task.set(
                {
                    "task": task,
                    "gender": gender,
                    "time": now.isoformat(),
                    "message_id": proof_message.id,
                }
            )
            await conf_user.last_request.set(now.isoformat())

            stats = await conf_guild.stats()
            entry = stats.setdefault(str(user.id), {"male": 0, "female": 0})
            entry[gender] = entry.get(gender, 0) + 1
            await conf_guild.stats.set(stats)

            await self.log(
                guild,
                "🎯 Taak aangevraagd",
                f"{user.mention}\nCategorie: {gender}\nTaak: {task}",
            )

            await interaction.response.send_message(
                f"✅ Taak geplaatst in {proof_channel.mention}", ephemeral=True
            )

    # =========================
    # PROOF REVIEW
    # =========================
    async def handle_proof_review(self, interaction: discord.Interaction, approved: bool):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message(
                "❌ Dit werkt alleen binnen een server.", ephemeral=True
            )

        if not await self.can_approve(interaction.user):
            return await interaction.response.send_message(
                f"❌ Je mag geen bewijs {'goedkeuren' if approved else 'afkeuren'}.",
                ephemeral=True,
            )

        async with self.lock_for(f"review:{interaction.message.id}"):
            conf_guild = self.config.guild(guild)
            reviews = await conf_guild.reviews()
            entry = reviews.pop(str(interaction.message.id), None)

            if entry is None:
                return await interaction.response.send_message(
                    "ℹ️ Dit bewijs is al beoordeeld.", ephemeral=True
                )

            await conf_guild.reviews.set(reviews)

            user_id = self.review_user_id(entry)
            task_time = entry.get("task_time") if isinstance(entry, dict) else None

            if user_id is None:
                return await interaction.response.send_message(
                    "ℹ️ Dit bewijs is al beoordeeld.", ephemeral=True
                )

            member = guild.get_member(user_id)
            now = datetime.now(timezone.utc)

            if member is not None:
                conf_user = self.config.user(member)
                current = await conf_user.active_task()
                # Alleen de beoordeelde taak vrijgeven, niet een inmiddels nieuwe.
                if not current or (task_time and current.get("time") == task_time):
                    await conf_user.active_task.set({})
                # Goedgekeurd: cooldown vrij. Afgekeurd: cooldown gaat nu in.
                await conf_user.last_request.set(None if approved else now.isoformat())

            if interaction.message is not None:
                try:
                    await interaction.message.edit(view=ProofReviewView(self, disabled=True))
                except discord.HTTPException:
                    pass

            target = member.mention if member is not None else f"<@{user_id}>"

            if approved:
                title = "✅ Bewijs goedgekeurd"
                text = f"✅ Bewijs goedgekeurd voor {target}."
            else:
                title = "❌ Bewijs afgekeurd"
                text = f"❌ Bewijs afgekeurd voor {target}. Cooldown gaat opnieuw in."

            await interaction.response.send_message(text)
            await self.log(guild, title, f"{interaction.user.mention} → {target}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        conf_guild = self.config.guild(message.guild)
        proof_channel_id = await conf_guild.proof_channel()
        if not proof_channel_id or message.channel.id != proof_channel_id:
            return

        active = await self.config.user(message.author).active_task()
        if not active:
            return

        # Bewijs moet een reply zijn op het taakbericht van deze taak.
        task_message_id = active.get("message_id")
        if task_message_id:
            reference = message.reference
            if reference is None or reference.message_id != task_message_id:
                await self.nudge_reply(message)
                return

        # Commando's zijn geen bewijs.
        if message.content:
            prefixes = await self.bot.get_valid_prefixes(message.guild)
            if any(message.content.startswith(prefix) for prefix in prefixes):
                return

        if not (message.content.strip() or message.attachments or message.stickers):
            return

        # Al een openstaande beoordeling voor deze gebruiker? Dan geen tweede embed.
        reviews = await conf_guild.reviews()
        if any(
            self.review_user_id(entry) == message.author.id for entry in reviews.values()
        ):
            return

        conf_user = self.config.user(message.author)
        task_time = active.get("time")

        # Bewijs is geleverd, dus de blokkade vervalt meteen. De beoordeling bepaalt
        # alleen nog of de cooldown opnieuw ingaat.
        await conf_user.active_task.set({})
        await conf_user.last_request.set(None)

        if not await conf_guild.approve_required():
            try:
                await message.add_reaction("✅")
            except discord.HTTPException:
                pass
            await self.log(
                message.guild,
                "✅ Bewijs automatisch goedgekeurd",
                f"{message.author.mention}",
            )
            return

        review_message = await message.channel.send(
            embed=discord.Embed(
                title="🛂 Bewijs ontvangen",
                description=(
                    f"{message.author.mention} heeft bewijs geleverd.\n"
                    f"[Open het bewijs]({message.jump_url})"
                ),
                color=PURPLE,
            ),
            view=ProofReviewView(self),
        )

        reviews[str(review_message.id)] = {
            "user_id": message.author.id,
            "task_time": task_time,
        }
        await conf_guild.reviews.set(reviews)

    # =========================
    # COMMANDS
    # =========================
    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def roulette(self, ctx: commands.Context):
        """Roulette hoofdcommando"""
        await ctx.send_help()

    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def setup(
        self,
        ctx,
        button_channel: discord.TextChannel,
        proof_channel: discord.TextChannel,
    ):
        """Stel knoppen- en bewijskanaal in en plaats het taakbericht."""
        g = self.config.guild(ctx.guild)
        await g.button_channel.set(button_channel.id)
        await g.proof_channel.set(proof_channel.id)

        await button_channel.send(
            embed=discord.Embed(
                title="🎰 Roulette",
                description="Klik op een knop om een taak te krijgen.",
                color=PURPLE,
            ),
            view=RouletteView(self),
        )
        await ctx.send("✅ Roulette ingesteld.")

    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def logchannel(self, ctx, channel: discord.TextChannel):
        """Stel het logkanaal in."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send("✅ Logkanaal ingesteld.")

    @roulette.command(name="approve")
    @commands.admin_or_permissions(manage_guild=True)
    async def approve_mode(self, ctx, mode: str):
        """Zet verplichte goedkeuring aan of uit (`on`/`off`)."""
        mode = mode.lower()
        if mode not in ("on", "off"):
            return await ctx.send("Gebruik `on` of `off`.")
        await self.config.guild(ctx.guild).approve_required.set(mode == "on")
        await ctx.send(f"✅ Approve {'ingeschakeld' if mode == 'on' else 'uitgeschakeld'}.")

    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def approverole(self, ctx, *, role: str):
        """Rol die bewijs mag beoordelen. Gebruik `remove` om te wissen."""
        if role.lower() == "remove":
            await self.config.guild(ctx.guild).approve_role.set(None)
            return await ctx.send("✅ Approverol verwijderd.")

        role_obj = discord.utils.get(ctx.guild.roles, name=role)
        if role_obj is None:
            try:
                role_obj = ctx.guild.get_role(int(role))
            except ValueError:
                role_obj = None
        if role_obj is None:
            return await ctx.send("❌ Rol niet gevonden. Gebruik naam of ID.")

        await self.config.guild(ctx.guild).approve_role.set(role_obj.id)
        await ctx.send(f"✅ {role_obj.name} mag nu bewijs beoordelen.")

    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def addtask(self, ctx, gender: str, *, task: str):
        """Voeg een taak toe (`male` of `female`)."""
        gender = gender.lower()
        if gender not in GENDERS:
            return await ctx.send("Gebruik `male` of `female`.")
        self.tasks.setdefault(gender, []).append(task.strip())
        self.save_tasks()
        await ctx.send(f"✅ Taak toegevoegd aan {gender}.")

    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def removetask(self, ctx, gender: str, index: int):
        """Verwijder een taak op index (`roulette tasks` toont de nummers)."""
        gender = gender.lower()
        pool = self.tasks.get(gender)
        if pool is None:
            return await ctx.send("Gebruik `male` of `female`.")
        try:
            removed = pool.pop(index)
        except IndexError:
            return await ctx.send("❌ Ongeldige index.")
        self.save_tasks()
        await ctx.send(f"🗑️ Verwijderd: {removed}")

    @roulette.command(name="tasks")
    async def list_tasks(self, ctx):
        """Toon alle taken met hun index."""
        embed = discord.Embed(title="📋 Takenlijst", color=PURPLE)
        for gender, label in (("male", "Mannen"), ("female", "Vrouwen")):
            pool = self.tasks.get(gender, [])
            value = "\n".join(f"`{i}` {task}" for i, task in enumerate(pool)) or "Geen"
            embed.add_field(name=label, value=value[:1024])
        await ctx.send(embed=embed)

    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def cooldown(self, ctx, hours: int):
        """Stel de cooldown in uren in (0–8760)."""
        if not 0 <= hours <= 8760:
            return await ctx.send("❌ Gebruik een aantal uren tussen 0 en 8760.")
        await self.config.guild(ctx.guild).cooldown_hours.set(hours)
        await ctx.send(f"⏱️ Cooldown ingesteld op {hours} uur.")

    @roulette.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def reset(self, ctx, member: discord.Member = None):
        """Breek de lopende taak van een lid af en wis de cooldown."""
        target = member or ctx.author
        conf_user = self.config.user(target)
        await conf_user.active_task.set({})
        await conf_user.last_request.set(None)

        # Openstaande reviews van dit lid opruimen.
        conf_guild = self.config.guild(ctx.guild)
        reviews = await conf_guild.reviews()
        stale = [
            message_id
            for message_id, entry in reviews.items()
            if self.review_user_id(entry) == target.id
        ]
        for message_id in stale:
            reviews.pop(message_id, None)
        if stale:
            await conf_guild.reviews.set(reviews)

        await ctx.send(f"♻️ Lopende taak van {target.mention} afgebroken, cooldown gewist.")

    @roulette.command()
    async def stats(self, ctx):
        """Toon statistieken per gebruiker."""
        stats = await self.config.guild(ctx.guild).stats()
        if not stats:
            return await ctx.send("❌ Geen data.")

        lines = []
        for uid, data in stats.items():
            try:
                member = ctx.guild.get_member(int(uid))
            except (TypeError, ValueError):
                member = None
            name = member.display_name if member is not None else f"Onbekend ({uid})"
            lines.append(f"**{name}** → M:{data.get('male', 0)} V:{data.get('female', 0)}")

        embed = discord.Embed(
            title="📊 Roulette Statistieken",
            description="\n".join(lines)[:4000],
            color=PURPLE,
        )
        await ctx.send(embed=embed)

    @roulette.command()
    async def settings(self, ctx):
        """Toon de huidige instellingen."""
        g = self.config.guild(ctx.guild)
        button_channel = await g.button_channel()
        proof_channel = await g.proof_channel()
        log_channel = await g.log_channel()
        approve_role = await g.approve_role()

        embed = discord.Embed(title="⚙️ Instellingen", color=PURPLE)
        embed.add_field(
            name="Knoppenkanaal",
            value=f"<#{button_channel}>" if button_channel else "Niet ingesteld",
        )
        embed.add_field(
            name="Bewijskanaal",
            value=f"<#{proof_channel}>" if proof_channel else "Niet ingesteld",
        )
        embed.add_field(
            name="Logkanaal",
            value=f"<#{log_channel}>" if log_channel else "Niet ingesteld",
        )
        embed.add_field(name="Cooldown (uur)", value=str(await g.cooldown_hours()))
        embed.add_field(name="Approve vereist", value=str(await g.approve_required()))
        embed.add_field(
            name="Approve rol",
            value=f"<@&{approve_role}>" if approve_role else "Niet ingesteld",
        )
        await ctx.send(embed=embed)
