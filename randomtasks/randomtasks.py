
import json
import random
from redbot.core import commands, Config
import discord
from discord.ui import View, Button
from pathlib import Path

class RandomTasks(commands.Cog):
    """Geeft random taken per server en beheert ze via een GUI."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987654322)
        self.config.register_guild(tasks=[])
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
            async def random_task(self, interaction, button):
                tasks = await self.cog.get_tasks(interaction.guild.id)
                taak = random.choice(tasks)
                embed = discord.Embed(
                    title="🎲 Random Taak",
                    description=taak,
                    color=discord.Color.purple()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            @discord.ui.button(label="➕ Taak toevoegen", style=discord.ButtonStyle.success)
            async def add_task(self, interaction, button):
                await interaction.response.send_message("Voer de taak in om toe te voegen:")

                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel

                msg = await self.cog.bot.wait_for("message", check=check)
                tasks = await self.cog.get_tasks(interaction.guild.id)
                tasks.append(msg.content)
                await self.cog.config.guild(interaction.guild).tasks.set(tasks)
                await interaction.followup.send(f"✅ Taak toegevoegd: **{msg.content}**", ephemeral=True)

            @discord.ui.button(label="🗑 Taak verwijderen", style=discord.ButtonStyle.danger)
            async def remove_task(self, interaction, button):
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
            async def list_tasks(self, interaction, button):
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
