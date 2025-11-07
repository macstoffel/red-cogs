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
        self.config.register_guild(tasks=[], log_channel_id=None)
        self.data_path = Path(__file__).parent / "taken.json"

        if self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.default_tasks = data.get("tasks", [])
        else:
            self.default_tasks = []

        # ✅ Maak de GUI persistent (blijft werken bij bot-restart)
        # Door custom_ids te gebruiken op buttons kan Discord interacties blijven routeren.
        bot.add_view(self.PersistentTaskView(self))

    async def get_tasks(self, guild_id):
        tasks = await self.config.guild_from_id(guild_id).tasks()
        if not tasks:
            await self.config.guild_from_id(guild_id).tasks.set(self.default_tasks)
            return self.default_tasks
        return tasks

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
        embed = discord.Embed(
            title="📌 Taken Manager (Server)",
            description=f"Taken opgeslagen voor **{ctx.guild.name}**.\nKies een optie.",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed, view=self.PersistentTaskView(self))

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

            #await interaction.response.send_message("✅ Taak verstuurd!", ephemeral=True)
            await self.cog._log_assignment(interaction.guild, interaction.user, taak, interaction.channel)

        @discord.ui.button(label="➕ Taak toevoegen", style=discord.ButtonStyle.success, custom_id="task_add_button")
        async def add_task(self, interaction: discord.Interaction, button):
            if not self.cog._is_mod(interaction.user):
                return await interaction.response.send_message("❌ Alleen moderators of hoger kunnen taken toevoegen.", ephemeral=True)

            await interaction.response.send_message("Voer de taak in om toe te voegen:")

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            msg = await self.cog.bot.wait_for("message", check=check)
            tasks = await self.cog.get_tasks(interaction.guild.id)
            tasks.append(msg.content)
            await self.cog.config.guild(interaction.guild).tasks.set(tasks)

            await interaction.followup.send(f"✅ Taak toegevoegd: **{msg.content}**", ephemeral=True)

        @discord.ui.button(label="🗑 Taak verwijderen", style=discord.ButtonStyle.danger, custom_id="task_remove_button")
        async def remove_task(self, interaction: discord.Interaction, button):
            if not self.cog._is_mod(interaction.user):
                return await interaction.response.send_message("❌ Alleen moderators of hoger kunnen taken verwijderen.", ephemeral=True)

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
        await self.config.guild(ctx.guild).tasks.set(tasks)
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
        await self.config.guild(ctx.guild).tasks.set(tasks)
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


async def setup(bot):
    await bot.add_cog(RandomTasks(bot))
