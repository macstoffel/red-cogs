import json
import random
import asyncio
from pathlib import Path
from typing import Optional, List, Tuple

import discord
from discord import Embed
from discord.ui import View, button, Button
from redbot.core import commands, Config


class AnswerView(View):
    def __init__(self, answers: List[str]):
        super().__init__(timeout=None)
        self.answers = answers
        self.selected: Optional[Tuple[int, int]] = None  # (user_id, answer_index)

    async def _handle(self, interaction: discord.Interaction, index: int):
        if self.selected is not None:
            # already answered
            await interaction.response.send_message("Er is al geantwoord.", ephemeral=True)
            return
        self.selected = (interaction.user.id, index)
        # disable buttons
        for child in self.children:
            child.disabled = True
        try:
            # edit the original message via the interaction response to acknowledge
            try:
                await interaction.response.edit_message(view=self)
            except Exception:
                # fallback to editing the message object if response.edit_message fails
                if interaction.message:
                    await interaction.message.edit(view=self)
        except Exception:
            pass
        # stop the view so waiters resume
        self.stop()

    @button(label="Antwoord 1", style=discord.ButtonStyle.primary)  # placeholders; will be edited
    async def _b1(self, button_obj: Button, interaction: discord.Interaction):
        await self._handle(interaction, 0)

    @button(label="Antwoord 2", style=discord.ButtonStyle.primary)
    async def _b2(self, button_obj: Button, interaction: discord.Interaction):
        await self._handle(interaction, 1)

    @button(label="Antwoord 3", style=discord.ButtonStyle.primary)
    async def _b3(self, button_obj: Button, interaction: discord.Interaction):
        await self._handle(interaction, 2)


class Quiz(commands.Cog):
    """Simple quiz cog: JSON-backed questions, button answers, per-guild scores."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987654321012)
        # only keep play_channel in Config; scores are persisted in vragen.json
        self.config.register_guild(play_channel_id=None)

        self.data_file = Path(__file__).parent / "vragen.json"
        # in-memory structures; _load_questions will populate both
        self.questions: dict = {}
        self.scores: dict = {}
        self._load_questions()

        # track background tasks per guild so only one quiz loop runs per guild
        self.active_tasks: dict[int, asyncio.Task] = {}

    def _load_questions(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.questions = data.get("vragen", {}) or {}
                # scores stored as: { "<guild_id>": { "<user_id>": score, ... }, ... }
                self.scores = data.get("scores", {}) or {}
            except Exception:
                self.questions = {}
                self.scores = {}
        else:
            # fallback default
            self.questions = {
                "Wat is 2+2?": {"antwoorden": ["3", "4", "5"], "juist": 1}
            }
            self.scores = {}

    def _save_questions(self):
        # persist both questions and scores into the JSON file
        data = {"vragen": self.questions, "scores": self.scores}
        # preserve leiderscores if present in file
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
        else:
            existing = {}
        existing.update(data)
        tmp = self.data_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
            f.flush()
        tmp.replace(self.data_file)

    async def _get_channel_for_guild(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        cid = await self.config.guild(guild).play_channel_id()
        if cid:
            return guild.get_channel(int(cid))
        return None

    async def _update_score(self, guild: discord.Guild, user_id: int, delta: int):
        gid = str(guild.id)
        guild_scores = self.scores.get(gid, {})
        guild_scores[str(user_id)] = guild_scores.get(str(user_id), 0) + int(delta)
        self.scores[gid] = guild_scores
        try:
            self._save_questions()
        except Exception:
            pass

    async def _get_scores(self, guild: discord.Guild) -> dict:
        return self.scores.get(str(guild.id), {})

    @commands.group()
    async def quiz(self, ctx):
        """Quiz commands group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Gebruik subcommands: start / stop / setplaychannel / top10 / score / addquestion")

    @quiz.command(name="setplaychannel")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def setplaychannel(self, ctx, channel: discord.TextChannel):
        """Stel het kanaal in waar de quiz vragen gepost worden."""
        await self.config.guild(ctx.guild).play_channel_id.set(channel.id)
        await ctx.send(f"Quiz-kanaal ingesteld op {channel.mention}")

    @quiz.command(name="start")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def start(self, ctx):
        """Start automatische vragen plaatsen in de ingestelde kanaal."""
        guild_id = ctx.guild.id
        if guild_id in self.active_tasks:
            return await ctx.send("Quiz is al gestart op deze server.")
        channel = await self._get_channel_for_guild(ctx.guild) or ctx.channel
        task = asyncio.create_task(self._quiz_loop(ctx.guild, channel))
        self.active_tasks[guild_id] = task
        await ctx.send(f"Quiz gestart in {channel.mention}")

    @quiz.command(name="stop")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def stop(self, ctx):
        guild_id = ctx.guild.id
        task = self.active_tasks.get(guild_id)
        if not task:
            return await ctx.send("Er loopt geen quiz op deze server.")
        task.cancel()
        try:
            await task
        except Exception:
            pass
        del self.active_tasks[guild_id]
        await ctx.send("Quiz gestopt.")

    async def _quiz_loop(self, guild: discord.Guild, channel: discord.TextChannel):
        # continuous loop: post a random question, wait for first button click, process, repeat
        try:
            while True:
                if not self.questions:
                    await channel.send("Geen vragen beschikbaar.")
                    return
                vraag = random.choice(list(self.questions.keys()))
                data = self.questions[vraag]
                antwoorden = data.get("antwoorden", [])
                correct_idx = int(data.get("juist", 0))

                embed = Embed(title=vraag, description="Klik op één van de knoppen om te antwoorden.", color=discord.Color.purple())
                for i, a in enumerate(antwoorden):
                    embed.add_field(name=f"Antwoord {i+1}", value=a, inline=False)

                view = AnswerView(antwoorden)
                # set button labels to actual answers
                try:
                    view.children[0].label = antwoorden[0]
                    view.children[1].label = antwoorden[1]
                    view.children[2].label = antwoorden[2]
                except Exception:
                    pass

                msg = await channel.send(embed=embed, view=view)

                # wait until someone answers (no timeout)
                try:
                    await view.wait()
                except asyncio.CancelledError:
                    # view.wait was cancelled because the task was cancelled; try to cleanup view
                    try:
                        view.stop()
                    except Exception:
                        pass
                    raise

                if view.selected is None:
                    # shouldn't happen, but continue
                    await channel.send("Er is geen antwoord geregistreerd.")
                    continue

                user_id, ans_idx = view.selected
                guild_obj = guild
                member = guild_obj.get_member(user_id)
                if ans_idx == correct_idx:
                    await self._update_score(guild_obj, user_id, 1)
                    res_embed = Embed(title="Juist!", description=f"{member.mention if member else user_id} kreeg +1 punt.", color=discord.Color.purple())
                else:
                    await self._update_score(guild_obj, user_id, -1)
                    res_embed = Embed(title="Niet juist...", description=f"{member.mention if member else user_id} kreeg -1 punt.", color=discord.Color.purple())
                await channel.send(embed=res_embed)
                # small delay to avoid message collisions
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            # allow graceful cancellation
            return
        except Exception:
            # log other unexpected exceptions but don't crash the loop permanently
            try:
                await channel.send("Er is een fout opgetreden in de quiz loop.")
            except Exception:
                pass
            return
        finally:
            # cleanup active task entry if present
            try:
                self.active_tasks.pop(guild.id, None)
            except Exception:
                pass

    @quiz.command(name="top10")
    @commands.guild_only()
    async def top10(self, ctx):
        scores = await self._get_scores(ctx.guild)
        items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        embed = Embed(title="Top 10", color=discord.Color.purple())
        for i, (uid, score) in enumerate(items):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else str(uid)
            embed.add_field(name=f"Rang {i+1}", value=f"{name} — {score} punten", inline=False)
        await ctx.send(embed=embed)

    @quiz.command(name="score")
    @commands.guild_only()
    async def score(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        scores = await self._get_scores(ctx.guild)
        score = scores.get(str(member.id), 0)
        await ctx.send(embed=Embed(title="Score", description=f"{member.display_name} heeft {score} punten.", color=discord.Color.purple()))

    @quiz.command(name="addquestion")
    @commands.guild_only()
    async def addquestion(self, ctx):
        """Interactief een vraag toevoegen (vraag + 3 antwoorden + juist index)."""
        author = ctx.author
        def msg_check(m: discord.Message):
            return m.author.id == author.id and m.channel == ctx.channel

        await ctx.send("Stuur de vraag (tekst):")
        try:
            q_msg = await self.bot.wait_for("message", check=msg_check, timeout=120)
            vraag = q_msg.content.strip()
            await ctx.send("Antwoord 1:")
            a1 = (await self.bot.wait_for("message", check=msg_check, timeout=120)).content.strip()
            await ctx.send("Antwoord 2:")
            a2 = (await self.bot.wait_for("message", check=msg_check, timeout=120)).content.strip()
            await ctx.send("Antwoord 3:")
            a3 = (await self.bot.wait_for("message", check=msg_check, timeout=120)).content.strip()
            await ctx.send("Welk antwoord is juist? Stuur 1, 2 of 3:")
            correct_msg = await self.bot.wait_for("message", check=msg_check, timeout=120)
            correct = int(correct_msg.content.strip()) - 1
            if correct not in (0, 1, 2):
                return await ctx.send("Ongeldige juiste index; annuleer.")
        except asyncio.TimeoutError:
            return await ctx.send("Timeout — beantwoord niet op tijd.")
        except Exception as e:
            return await ctx.send(f"Fout bij toevoegen: {e}")

        self.questions[vraag] = {"antwoorden": [a1, a2, a3], "juist": int(correct)}
        try:
            self._save_questions()
        except Exception:
            pass
        await ctx.send("Vraag toegevoegd.")


async def setup(bot):
    await bot.add_cog(Quiz(bot))
