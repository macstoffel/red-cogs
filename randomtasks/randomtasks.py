import json
import random
from redbot.core import commands, Config
import discord
from discord.ui import View, Button
from pathlib import Path
import datetime
import os
import logging
from typing import Optional
import asyncio

class RandomTasks(commands.Cog):
    """Geeft random taken per server en beheert ze via een GUI."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987654322)
        self.config.register_guild(tasks=[], log_channel_id=None, custom_title=None)
        self.data_path = Path(__file__).parent / "taken.json"
        self.guild_data_dir = Path(__file__).parent / "guild_data"
        os.makedirs(self.guild_data_dir, exist_ok=True)

        # logger
        self.logger = logging.getLogger("red.randomtasks")
        # ensure persistent view re-registered
        try:
            bot.add_view(self.PersistentTaskView(self))
        except Exception:
            # ignore if view already added
            pass

        if self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.default_tasks = data.get("tasks", [])
        else:
            self.default_tasks = []

    # ---- New: per-guild file helpers ----
    def _guild_tasks_file(self, guild_id: int) -> Path:
        return self.guild_data_dir / f"{guild_id}_tasks.json"

    async def load_guild_tasks(self, guild_id: int):
        path = self._guild_tasks_file(guild_id)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "tasks" in data:
                    return data["tasks"]
            except Exception as e:
                self.logger.exception("Failed to load guild tasks for %s: %s", guild_id, e)
                # fall back to defaults
                return list(self.default_tasks)
        # file doesn't exist -> create with defaults
        await self.save_guild_tasks(guild_id, list(self.default_tasks))
        return list(self.default_tasks)

    async def save_guild_tasks(self, guild_id: int, tasks):
        """Atomic write to per-guild JSON. Returns True on success."""
        path = self._guild_tasks_file(guild_id)
        tmp_path = path.with_suffix(".tmp")
        try:
            os.makedirs(path.parent, exist_ok=True)
            # write to temp file then rename
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            self.logger.debug("Saved tasks for guild %s -> %s", guild_id, path)
            return True
        except Exception as e:
            # cleanup temp file if present
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass
            self.logger.exception("Failed to save guild tasks for %s: %s", guild_id, e)
            return False

    async def get_tasks(self, guild_id):
        # override previous behavior: load from per-guild JSON
        return await self.load_guild_tasks(guild_id)
    # ---- end per-guild helpers ----

    def _is_mod(self, member: discord.Member) -> bool:
        perms = member.guild_permissions
        return bool(
            perms.administrator
            or perms.manage_guild
            or perms.kick_members
            or perms.manage_messages
            or perms.manage_roles
        )

    async def _log_assignment(self, guild: discord.Guild, user: discord.Member, task: str, ctx_channel: discord.TextChannel = None):
        try:
            log_chan_id = await self.config.guild(guild).log_channel_id()
            if not log_chan_id:
                return
            ch = guild.get_channel(int(log_chan_id))
            if ch is None:
                return
            embed = discord.Embed(
                title="Taak toegewezen",
                color=discord.Color.purple(),
                timestamp=datetime.datetime.utcnow(),
            )
            member = guild.get_member(int(user.id)) if hasattr(user, "id") else None
            display_name = member.display_name if member else getattr(user, "display_name", getattr(user, "name", str(user)))
            embed.add_field(name="Gebruiker", value=f"{display_name} ({user.id})", inline=False)
            embed.add_field(name="Taak", value=task, inline=False)
            if ctx_channel:
                embed.add_field(name="Aangevraagd in", value=f"{ctx_channel.mention} ({ctx_channel.id})", inline=False)
            await ch.send(embed=embed)
        except Exception:
            return

    # ✅ Random taak via command, verdwijnt na 60s
    @commands.command()
    async def taak(self, ctx):
        tasks = await self.get_tasks(ctx.guild.id)
        taak = random.choice(tasks)
        embed = discord.Embed(
            title=f"🎲 Random Taak voor\n {ctx.author.mention}:",
            description=taak,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Aangevraagd door {ctx.author}")

        msg = await ctx.send(embed=embed, delete_after=60)
        await self._log_assignment(ctx.guild, ctx.author, taak, ctx.channel)

    # ✅ Hoofd-GUI command (persistent view)
    @commands.command()
    async def taakgui(self, ctx):
        custom = await self.config.guild(ctx.guild).custom_title()
        title = custom or f"📌 Taken Manager — {ctx.guild.name}"
        embed = discord.Embed(
            title=title,
            description=f"Taken opgeslagen voor **{ctx.guild.name}**.\nKies een optie.",
            color=discord.Color.purple()
        )
        # Toon volledige GUI alleen voor moderators of hoger; normale gebruikers zien alleen de
        # knop voor "Random Taak".
        if self._is_mod(ctx.author):
            view = self.PersistentTaskView(self)
        else:
            view = self.PublicTaskView(self)
        await ctx.send(embed=embed, view=view)

    # ✅ PERSISTENT VIEW — timeout=None + custom_ids + herladen bij restart
    class PersistentTaskView(View):
        def __init__(self, parent_cog):
            super().__init__(timeout=None)  # ✅ oneindig actief
            self.cog = parent_cog

        @discord.ui.button(label="🎲 Random Taak", style=discord.ButtonStyle.primary, custom_id="task_random_button")
        async def random_task(self, interaction: discord.Interaction, button):
            tasks = await self.cog.get_tasks(interaction.guild.id)
            if not tasks:
                return await interaction.response.send_message("Geen taken beschikbaar.", ephemeral=True)
            taak = random.choice(tasks)

            embed = discord.Embed(
                title=f"🎲 Random Taak voor\n {interaction.user.display_name}:",
                description=taak,
                color=discord.Color.purple()
            )

            # ✅ Bericht zichtbaar voor iedereen, maar auto-delete na 60s
            msg = await interaction.channel.send(embed=embed, delete_after=60)

            # acknowledge interaction silently (geen extra bericht)
            await interaction.response.defer(ephemeral=True)
            await self.cog._log_assignment(interaction.guild, interaction.user, taak, interaction.channel)

        @discord.ui.button(label="➕ Taak toevoegen", style=discord.ButtonStyle.success, custom_id="task_add_button")
        async def add_task(self, interaction: discord.Interaction, button):
            if not self.cog._is_mod(interaction.user):
                return await interaction.response.send_message("❌ Alleen moderators of hoger kunnen taken toevoegen.", ephemeral=True)

            await interaction.response.send_message("Voer de taak in om toe te voegen (je hebt 120s):", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await self.cog.bot.wait_for("message", check=check, timeout=120)
            except asyncio.TimeoutError:
                return await interaction.followup.send("⏱️ Time-out: taak toevoegen geannuleerd.", ephemeral=True)

            task_text = msg.content.strip()
            if not task_text:
                return await interaction.followup.send("❌ Lege taak, afgebroken.", ephemeral=True)

            tasks = await self.cog.get_tasks(interaction.guild.id)
            tasks.append(task_text)
            ok = await self.cog.save_guild_tasks(interaction.guild.id, tasks)
            if not ok:
                # probeer rollback in-memory
                try:
                    tasks.pop()
                except Exception:
                    pass
                return await interaction.followup.send("❌ Opslaan mislukt — bekijk botlogs.", ephemeral=True)

            await interaction.followup.send(f"✅ Taak toegevoegd: **{task_text}**", ephemeral=True)

        @discord.ui.button(label="🗑 Taak verwijderen", style=discord.ButtonStyle.danger, custom_id="task_remove_button")
        async def remove_task(self, interaction: discord.Interaction, button):
            if not self.cog._is_mod(interaction.user):
                return await interaction.response.send_message("❌ Alleen moderators of hoger kunnen taken verwijderen.", ephemeral=True)

            tasks = await self.cog.get_tasks(interaction.guild.id)
            if not tasks:
                return await interaction.response.send_message("Geen taken om te verwijderen.", ephemeral=True)

            lijst = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
            await interaction.response.send_message(f"Welke wil je verwijderen?\n{lijst}\nTyp het nummer (120s):", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await self.cog.bot.wait_for("message", check=check, timeout=120)
            except asyncio.TimeoutError:
                return await interaction.followup.send("⏱️ Time-out: verwijderen geannuleerd.", ephemeral=True)

            try:
                index = int(msg.content) - 1
                if index < 0 or index >= len(tasks):
                    raise ValueError("out of range")
                removed = tasks.pop(index)
            except Exception:
                return await interaction.followup.send("❌ Ongeldig nummer.", ephemeral=True)

            ok = await self.cog.save_guild_tasks(interaction.guild.id, tasks)
            if not ok:
                # rollback
                try:
                    tasks.insert(index, removed)
                except Exception:
                    pass
                return await interaction.followup.send("❌ Opslaan mislukt — wijzigingen niet doorgevoerd.", ephemeral=True)

            await interaction.followup.send(f"🗑 Verwijderd: **{removed}**", ephemeral=True)

        @discord.ui.button(label="📋 Takenlijst", style=discord.ButtonStyle.secondary, custom_id="task_list_button")
        async def list_tasks(self, interaction: discord.Interaction, button):
            if not self.cog._is_mod(interaction.user):
                return await interaction.response.send_message("❌ Alleen moderators of hoger mogen de takenlijst zien.", ephemeral=True)

            tasks = await self.cog.get_tasks(interaction.guild.id)
            if not tasks:
                return await interaction.response.send_message("Geen taken!", ephemeral=True)

            embed = discord.Embed(
                title=f"📋 Takenlijst — {interaction.guild.name}",
                description="\n".join([f"- {t}" for t in tasks]),
                color=discord.Color.purple()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Public view: alleen de Random Taak knop zichtbaar voor normale gebruikers
    class PublicTaskView(View):
        def __init__(self, parent_cog):
            super().__init__(timeout=None)
            self.cog = parent_cog

        @discord.ui.button(label="🎲 Random Taak", style=discord.ButtonStyle.primary, custom_id="task_random_public")
        async def random_task(self, interaction: discord.Interaction, button):
            tasks = await self.cog.get_tasks(interaction.guild.id)
            if not tasks:
                return await interaction.response.send_message("Geen taken beschikbaar.", ephemeral=True)
            taak = random.choice(tasks)
            embed = discord.Embed(
                title=f"🎲 Random Taak voor\n {interaction.user.display_name}:",
                description=taak,
                color=discord.Color.purple()
            )
            await interaction.channel.send(embed=embed, delete_after=60)
            await interaction.response.defer(ephemeral=True)
            await self.cog._log_assignment(interaction.guild, interaction.user, taak, interaction.channel)

    # --- Extra commands blijven hetzelfde ---
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taaklogset(self, ctx, channel: discord.TextChannel = None):
        await self.config.guild(ctx.guild).log_channel_id.set(channel.id if channel else None)
        await ctx.send(f"✅ Logkanaal ingesteld: {channel.mention if channel else 'Geen (uit)'}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taakadd(self, ctx, *, taak_text: str):
        if not self._is_mod(ctx.author):
            return await ctx.send("❌ Alleen moderators of hoger mogen taken beheren.")
        tasks = await self.get_tasks(ctx.guild.id)
        tasks.append(taak_text)
        await self.save_guild_tasks(ctx.guild.id, tasks)
        await ctx.send(f"✅ Taak toegevoegd: **{taak_text}**")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taakremove(self, ctx, index: int):
        if not self._is_mod(ctx.author):
            return await ctx.send("❌ Alleen moderators of hoger mogen taken beheren.")
        tasks = await self.get_tasks(ctx.guild.id)
        try:
            removed = tasks.pop(index - 1)
        except Exception:
            return await ctx.send("❌ Ongeldig index-nummer.")
        await self.save_guild_tasks(ctx.guild.id, tasks)
        await ctx.send(f"🗑 Verwijderd: **{removed}**")

    @commands.guild_only()
    @commands.command()
    async def taaklist(self, ctx):
        if not self._is_mod(ctx.author):
            return await ctx.send("❌ Alleen moderators of hoger mogen de takenlijst inzien.")
        tasks = await self.get_tasks(ctx.guild.id)
        if not tasks:
            return await ctx.send("Geen taken!")
        embed = discord.Embed(
            title=f"📋 Takenlijst — {ctx.guild.name}",
            description="\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]),
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taaktitleset(self, ctx, *, title: Optional[str] = None):
        """Stel een custom titel in voor de GUI embed. Laat leeg om terug te gaan naar de standaard."""
        await self.config.guild(ctx.guild).custom_title.set(title)
        await ctx.send(f"✅ Custom titel ingesteld: {title if title else 'standaard'}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taakshowfile(self, ctx):
        """Debug: toon pad en (gedeeltelijke) inhoud van guild task-file."""
        path = self._guild_tasks_file(ctx.guild.id)
        exists = path.exists()
        msg = f"Pad: `{path}`\nBestaat: `{exists}`\n\n"
        if exists:
            try:
                txt = path.read_text(encoding="utf-8")
                # trim lange bestanden
                if len(txt) > 1900:
                    txt = txt[:1900] + "\n\n...[truncated]..."
                msg += f"**Inhoud:**\n```json\n{txt}\n```"
            except Exception as e:
                msg += f"Fout bij lezen: {e}"
        await ctx.send(msg)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taakdebugsave(self, ctx):
        """Forceer opslaan en rapporteer bestandspad / success. (uitgebreide debug)"""
        tasks = await self.get_tasks(ctx.guild.id)
        ok = await self.save_guild_tasks(ctx.guild.id, tasks)
        path = self._guild_tasks_file(ctx.guild.id)
        if ok and path.exists():
            await ctx.send(f"✅ Tasks opgeslagen: `{path}` (size: {path.stat().st_size} bytes)")
        else:
            # probeer last logger entries te tonen (als beschikbaar)
            await ctx.send("❌ Opslaan mislukt — check bot logs. Controleer permissies en pad.")


async def setup(bot):
    await bot.add_cog(RandomTasks(bot))
