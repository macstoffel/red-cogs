import json
import random
from redbot.core import commands, Config
import discord
from discord.ui import View, Button
from pathlib import Path
import datetime

class RandomTasks(commands.Cog):
    """Geeft random taken per server en beheert ze via een GUI."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987654322)
        # per-guild settings: tasks list + optional logging channel id
        self.config.register_guild(tasks=[], log_channel_id=None)
        self.data_path = Path(__file__).parent / "taken.json"

        if self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.default_tasks = data.get("tasks", [])
        else:
            self.default_tasks = []

    async def get_tasks(self, guild_id):
        tasks = await self.config.guild_from_id(guild_id).tasks()
        if not tasks:
            await self.config.guild_from_id(guild_id).tasks.set(self.default_tasks)
            return self.default_tasks
        return tasks

    def _is_mod(self, member: discord.Member) -> bool:
        """Basic moderator-or-higher check: admin or common mod perms."""
        perms = member.guild_permissions
        return bool(
            perms.administrator
            or perms.manage_guild
            or perms.kick_members
            or perms.manage_messages
            or perms.manage_roles
        )
    
    async def _log_assignment(self, guild: discord.Guild, user: discord.Member, task: str, ctx_channel: discord.TextChannel = None):
        """If a log channel is configured for the guild, post who got which task."""
        try:
            gid = guild.id
            log_chan_id = await self.config.guild_from_id(gid).log_channel_id()
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
            embed.add_field(name="Gebruiker", value=f"{user.mention} ({user.id})", inline=False)
            embed.add_field(name="Taak", value=task, inline=False)
            if ctx_channel:
                embed.add_field(name="Aangevraagd in", value=f"{ctx_channel.mention} ({ctx_channel.id})", inline=False)
            await ch.send(embed=embed)
        except Exception:
            # don't raise—logging is best-effort
            return


    @commands.command()
    async def taak(self, ctx):
        tasks = await self.get_tasks(ctx.guild.id)
        taak = random.choice(tasks)
        embed = discord.Embed(
            title="🎲 Random Taak",
            description=taak,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Aangevraagd door {ctx.author}")
        await ctx.send(embed=embed)
        # log assignment if configured
        await self._log_assignment(ctx.guild, ctx.author, taak, ctx.channel)

    @commands.command()
    async def taakgui(self, ctx):
        tasks = await self.get_tasks(ctx.guild.id)
        embed = discord.Embed(
            title="📌 Taken Manager (Server)",
            description=f"Taken opgeslagen voor **{ctx.guild.name}**.\nKies een optie.",
            color=discord.Color.purple()
        )

        class TaskView(View):
            def __init__(self, parent_cog):
                super().__init__(timeout=120)
                self.cog = parent_cog

            @discord.ui.button(label="🎲 Random Taak", style=discord.ButtonStyle.primary)
            async def random_task(self, interaction: discord.Interaction, button: Button):
                tasks = await self.cog.get_tasks(interaction.guild.id)
                if not tasks:
                    return await interaction.response.send_message("Geen taken beschikbaar.", ephemeral=True)
                taak = random.choice(tasks)
                embed = discord.Embed(
                    title="🎲 Random Taak",
                    description=taak,
                    color=discord.Color.purple()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                # log assignment
                await self.cog._log_assignment(interaction.guild, interaction.user, taak, interaction.channel)

            @discord.ui.button(label="➕ Taak toevoegen", style=discord.ButtonStyle.success)
            async def add_task(self, interaction: discord.Interaction, button: Button):
                # only moderators or higher may add
                if not self.cog._is_mod(interaction.user):
                    return await interaction.response.send_message("❌ Alleen moderators of hoger mogen taken beheren.", ephemeral=True)

                await interaction.response.send_message("Voer de taak in om toe te voegen:")

                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel

                msg = await self.cog.bot.wait_for("message", check=check)
                tasks = await self.cog.get_tasks(interaction.guild.id)
                tasks.append(msg.content)
                await self.cog.config.guild(interaction.guild).tasks.set(tasks)
                await interaction.followup.send(f"✅ Taak toegevoegd: **{msg.content}**", ephemeral=True)

            @discord.ui.button(label="🗑 Taak verwijderen", style=discord.ButtonStyle.danger)
            async def remove_task(self, interaction: discord.Interaction, button: Button):
                # only moderators or higher may remove
                if not self.cog._is_mod(interaction.user):
                    return await interaction.response.send_message("❌ Alleen moderators of hoger mogen taken verwijderen.", ephemeral=True)

                tasks = await self.cog.get_tasks(interaction.guild.id)
                if not tasks:
                    return await interaction.response.send_message("Geen taken om te verwijderen.", ephemeral=True)

                lijst = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
                await interaction.response.send_message(f"Welke wil je verwijderen?\n{lijst}\nTyp het nummer:")

                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel

                msg = await self.cog.bot.wait_for("message", check=check)

                try:
                    index = int(msg.content) - 1
                    removed = tasks.pop(index)
                except:
                    return await interaction.followup.send("❌ Ongeldig nummer.", ephemeral=True)

                await self.cog.config.guild(interaction.guild).tasks.set(tasks)
                await interaction.followup.send(f"🗑 Verwijderd: **{removed}**", ephemeral=True)

            @discord.ui.button(label="📋 Takenlijst", style=discord.ButtonStyle.secondary)
            async def list_tasks(self, interaction: discord.Interaction, button: Button):
                # only moderators or higher may view the list
                if not self.cog._is_mod(interaction.user):
                    return await interaction.response.send_message("❌ Alleen moderators of hoger mogen de takenlijst inzien.", ephemeral=True)

                tasks = await self.cog.get_tasks(interaction.guild.id)
                if not tasks:
                    return await interaction.response.send_message("Geen taken!", ephemeral=True)

                embed = discord.Embed(
                    title=f"📋 Takenlijst — {interaction.guild.name}",
                    description="\n".join([f"- {t}" for t in tasks]),
                    color=discord.Color.purple()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        await ctx.send(embed=embed, view=TaskView(self))

    # --- Moderation / config commands ---
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taaklogset(self, ctx, channel: discord.TextChannel = None):
        """Stel het kanaal in waar taak-toewijzingen gelogd worden. Laat leeg om te verwijderen."""
        await self.config.guild(ctx.guild).log_channel_id.set(channel.id if channel else None)
        await ctx.send(f"✅ Logkanaal ingesteld: {channel.mention if channel else 'Geen (uit)'}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taakadd(self, ctx, *, taak_text: str):
        """Voeg snel een taak toe (moderator of hoger)."""
        if not self._is_mod(ctx.author):
            return await ctx.send("❌ Alleen moderators of hoger mogen taken beheren.")
        tasks = await self.get_tasks(ctx.guild.id)
        tasks.append(taak_text)
        await self.config.guild(ctx.guild).tasks.set(tasks)
        await ctx.send(f"✅ Taak toegevoegd: **{taak_text}**")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def taakremove(self, ctx, index: int):
        """Verwijder een taak op nummer (moderator of hoger). Gebruik [p]taaklist om nummers te zien."""
        if not self._is_mod(ctx.author):
            return await ctx.send("❌ Alleen moderators of hoger mogen taken beheren.")
        tasks = await self.get_tasks(ctx.guild.id)
        try:
            removed = tasks.pop(index - 1)
        except Exception:
            return await ctx.send("❌ Ongeldig index-nummer.")
        await self.config.guild(ctx.guild).tasks.set(tasks)
        await ctx.send(f"🗑 Verwijderd: **{removed}**")

    @commands.guild_only()
    @commands.command()
    async def taaklist(self, ctx):
        """Toon de takenlijst (alleen moderators of hoger)."""
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

# module setup
async def setup(bot):
    await bot.add_cog(RandomTasks(bot))
