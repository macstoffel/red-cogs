# woordspel_td.py
import discord
from redbot.core import commands
import enchant
import asyncio
import json
import os
import random
import time
from typing import Optional
from pathlib import Path

# pad naar het takenbestand binnen de cog-map (schrijfbaar)
DATA_PATH = Path(__file__).parent / "data" / "woordspel_td_tasks.json"
STATE_PATH = Path(__file__).parent / "data" / "woordspel_td_state.json"

class WoordspelTD(commands.Cog):
    """WoordspelTD - Woordspel met flirty dare-taken (groepscommand [p]ws)."""

    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        try:
            self.nl_dict = enchant.Dict("nl_NL")
        except enchant.errors.DictNotFoundError:
            self.nl_dict = None
        # zorg dat data-map binnen de cog-map bestaat en maak het bestand aan indien nodig
        data_dir = DATA_PATH.parent
        data_dir.mkdir(parents=True, exist_ok=True)
        if not DATA_PATH.exists():
            with DATA_PATH.open("w", encoding="utf-8") as f:
                json.dump({"default_tasks": [], "guilds": {}}, f, ensure_ascii=False, indent=2)
        self._load_tasks()

        # init runtime structures
        self.locks = {}
        self._timeout_tasks = {}

        # load persisted state (games + recreate timers)
        self._load_state()
        # recreate pending timeout tasks
        for gid, st in list(self.games.items()):
            expires = st.get("task_expires_at")
            if st.get("paused") and expires:
                remaining = expires - time.time()
                if remaining > 0:
                    self._timeout_tasks[gid] = asyncio.create_task(self._wait_timeout(gid, remaining))
                else:
                    # expired while offline -> handle as timeout
                    asyncio.create_task(self._task_completed(gid, False))

    # ----------------- Helpers -----------------
    def _get_state(self, guild_id: int) -> dict:
        return self.games.setdefault(guild_id, {
            "active": False,
            "channel_id": None,
            "current_score": 0,
            "high_score": 0,
            "last_word": None,
            "last_user_id": None,
            "goal_points": 10,
            "paused": False,
            "current_task_user_id": None,
            "task_channel_id": None,
            "task_timeout": 180
        })

    def _get_lock(self, guild_id: int):
        return self.locks.setdefault(guild_id, asyncio.Lock())

    def _load_tasks(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            try:
                self.tasks_data = json.load(f)
            except json.JSONDecodeError:
                self.tasks_data = {"default_tasks": [], "guilds": {}}
        self.tasks_data.setdefault("default_tasks", [])
        self.tasks_data.setdefault("guilds", {})

    def _save_tasks(self):
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.tasks_data, f, ensure_ascii=False, indent=2)

    def _guild_tasks(self, guild_id: int):
        g = self.tasks_data["guilds"].get(str(guild_id), {})
        return g.get("tasks", [])

    def _guild_task_channel(self, guild_id: int) -> Optional[int]:
        g = self.tasks_data["guilds"].get(str(guild_id), {})
        return g.get("task_channel")

    def _guild_timeout(self, guild_id: int) -> Optional[int]:
        g = self.tasks_data["guilds"].get(str(guild_id), {})
        return g.get("task_timeout")

    def make_embed(self, title=None, description=None):
        return discord.Embed(title=title, description=description, color=0x9B59B6)

    def _save_state(self):
        try:
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with STATE_PATH.open("w", encoding="utf-8") as f:
                json.dump(self.games, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # log if gewenst

    def _load_state(self):
        if STATE_PATH.exists():
            try:
                with STATE_PATH.open("r", encoding="utf-8") as f:
                    self.games = json.load(f)
                # convert keys back to int if needed
                self.games = {int(k): v for k, v in self.games.items()}
            except Exception:
                self.games = {}
        else:
            self.games = {}

    # ================= COMMANDS =================
    @commands.group(name="ws", invoke_without_command=True)
    async def ws(self, ctx):
        """Hoofdcommando voor het WoordspelTD."""
        embed = self.make_embed(
            title="🎮 WoordspelTD Help",
            description=(
                "**Spelcommando’s:**\n"
                "`[p]ws start [doelpunten]` - Start het spel\n"
                "`[p]ws stop` - Stop het spel\n"
                "`[p]ws totaal` - Toon huidige score\n"
                "`[p]ws highscore` - Toon hoogste score ooit\n\n"
                "**Taakbeheer (mods/admins):**\n"
                "`[p]ws settaskchannel #kanaal` - Stel taak-kanaal in\n"
                "`[p]ws settimeout <seconden>` - Stel timeout in\n"
                "`[p]ws addtask \"tekst\"` - Voeg guild-taak toe\n"
                "`[p]ws removetask <index>` - Verwijder taak\n"
                "`[p]ws listtasks` - Toon standaard- en guildtaken"
            )
        )
        await ctx.send(embed=embed)

    # --- Subcommands: spelbeheer ---
    @ws.command(name="start")
    async def ws_start(self, ctx, goal: int = 10):
        """Start het woordspel."""
        if self.nl_dict is None:
            await ctx.send("⚠️ Geen Nederlandse dictionary gevonden (pyenchant ontbreekt).")
            return
        st = self._get_state(ctx.guild.id)
        if st["active"]:
            await ctx.send("Er loopt al een spel.")
            return
        st.update({
            "active": True, "channel_id": ctx.channel.id,
            "current_score": 0, "goal_points": goal,
            "paused": False, "last_word": None, "last_user_id": None
        })
        tc = self._guild_task_channel(ctx.guild.id)
        if tc: st["task_channel_id"] = tc
        to = self._guild_timeout(ctx.guild.id)
        if to: st["task_timeout"] = to
        await ctx.send(embed=self.make_embed(
            title="🎮 WoordspelTD gestart!",
            description=f"Typ een woord dat begint met de laatste letter van het vorige.\nDoel: **{goal}** punten."
        ))

    @ws.command(name="stop")
    async def ws_stop(self, ctx):
        """Stop het spel."""
        st = self._get_state(ctx.guild.id)
        if not st["active"]:
            await ctx.send("Geen actief spel.")
            return
        st.update({"active": False, "paused": False, "current_task_user_id": None})
        t = self._timeout_tasks.get(ctx.guild.id)
        if t and not t.done(): t.cancel()
        await ctx.send("🛑 Het spel is gestopt.")

    @ws.command(name="totaal")
    async def ws_totaal(self, ctx):
        """Toon de huidige score."""
        st = self._get_state(ctx.guild.id)
        await ctx.send(f"Huidige score: {st['current_score']}")

    @ws.command(name="highscore")
    async def ws_highscore(self, ctx):
        """Toon de hoogste score ooit."""
        st = self._get_state(ctx.guild.id)
        await ctx.send(f"🏆 Hoogste score: {st['high_score']}")

    # --- Subcommands: takenbeheer ---
    @ws.command(name="settaskchannel")
    @commands.admin_or_permissions(manage_guild=True)
    async def ws_set_task_channel(self, ctx, channel: discord.TextChannel):
        """Stel het taak-kanaal in."""
        gid = str(ctx.guild.id)
        self.tasks_data["guilds"].setdefault(gid, {})["task_channel"] = channel.id
        self._save_tasks()
        st = self._get_state(ctx.guild.id)
        st["task_channel_id"] = channel.id
        await ctx.send(embed=self.make_embed(title="✅ Taak-kanaal ingesteld", description=f"{channel.mention}"))

    @ws.command(name="settimeout")
    @commands.admin_or_permissions(manage_guild=True)
    async def ws_set_timeout(self, ctx, seconds: int):
        """Stel de timeout in (in seconden)."""
        if seconds <= 0:
            await ctx.send("Timeout moet positief zijn.")
            return
        gid = str(ctx.guild.id)
        self.tasks_data["guilds"].setdefault(gid, {})["task_timeout"] = seconds
        self._save_tasks()
        st = self._get_state(ctx.guild.id)
        st["task_timeout"] = seconds
        await ctx.send(embed=self.make_embed(title="✅ Timeout ingesteld", description=f"{seconds} seconden."))

    @ws.command(name="addtask")
    @commands.admin_or_permissions(manage_guild=True)
    async def ws_add_task(self, ctx, *, text: str):
        """Voeg een guild-taak toe."""
        gid = str(ctx.guild.id)
        self.tasks_data["guilds"].setdefault(gid, {}).setdefault("tasks", []).append(text)
        self._save_tasks()
        await ctx.send(embed=self.make_embed(title="✅ Taak toegevoegd", description=text))

    @ws.command(name="removetask")
    @commands.admin_or_permissions(manage_guild=True)
    async def ws_remove_task(self, ctx, index: int):
        """Verwijder een guild-taak."""
        gid = str(ctx.guild.id)
        g = self.tasks_data["guilds"].get(gid, {}).get("tasks", [])
        if not g or index < 1 or index > len(g):
            await ctx.send("Ongeldige index.")
            return
        removed = g.pop(index - 1)
        self.tasks_data["guilds"][gid]["tasks"] = g
        self._save_tasks()
        await ctx.send(embed=self.make_embed(title="🗑️ Taak verwijderd", description=removed))

    @ws.command(name="listtasks")
    async def ws_list_tasks(self, ctx):
        """Toon standaard- en guildtaken."""
        gid = str(ctx.guild.id)
        default = self.tasks_data["default_tasks"]
        guild_t = self.tasks_data["guilds"].get(gid, {}).get("tasks", [])
        desc = "**Standaardtaken:**\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(default))
        desc += "\n\n**Guildtaken:**\n" + ("\n".join(f"{i+1}. {t}" for i, t in enumerate(guild_t)) or "_Geen taken_")
        await ctx.send(embed=self.make_embed(title="📜 Takenlijst", description=desc[:1990]))

    # --- Game mechanics: woordcontrole, taken, timeout ---
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot or not msg.guild: return
        st = self._get_state(msg.guild.id)

        # Taak-afhandeling en pauze-gedrag
        if st["paused"]:
            # als de toegewezen gebruiker in het taak-kanaal iets plaatst -> taak voltooid
            if msg.channel.id == st.get("task_channel_id") and msg.author.id == st.get("current_task_user_id"):
                await self._task_completed(msg.guild.id, True, msg)
                return
            # als iemand in het spelkanaal iets plaatst tijdens pauze -> verwijder en korte waarschuwing
            if msg.channel.id == st.get("channel_id"):
                try:
                    await msg.delete()
                except Exception:
                    pass
                assignee = msg.guild.get_member(st.get("current_task_user_id"))
                assignee_display = assignee.display_name if assignee else "de toegewezen speler"
                notice = await msg.channel.send(embed=self.make_embed(
                    description=f"⏸️ Het spel is gepauzeerd: {assignee_display} moet eerst de toegewezen taak uitvoeren."
                ))
                await asyncio.sleep(5)
                try:
                    await notice.delete()
                except Exception:
                    pass
                return
            # anders negeren
            return
        # niet actief of ander kanaal
        if not st["active"] or msg.channel.id != st["channel_id"]:
            return

        woord = msg.content.strip().lower()
        if len(woord.split()) != 1:
            await msg.delete()
            await msg.channel.send(embed=self.make_embed(description="❌ Het mag maar 1 woord zijn!"))
            return

        if st["last_user_id"] == msg.author.id:
            await msg.channel.send(embed=self.make_embed(description="❌ Je mag niet twee keer achter elkaar!"))
            return

        if st["last_word"] and not woord.startswith(st["last_word"][-1]):
            await self._invalid(msg, woord, f"moest beginnen met `{st['last_word'][-1]}`")
            return

        if not self.nl_dict.check(woord):
            await self._invalid(msg, woord, "is geen geldig Nederlands woord")
            return

        st["current_score"] += 1
        st["last_word"] = woord
        st["last_user_id"] = msg.author.id
        await msg.channel.send(embed=self.make_embed(
            description=f"✅ `{woord}` goed! Score: {st['current_score']} / {st['goal_points']}"
        ))

        if st["current_score"] >= st["goal_points"]:
            st["high_score"] = max(st["high_score"], st["current_score"])
            await msg.channel.send(embed=self.make_embed(title="🎉 Doel bereikt!", description="Het spel is voltooid."))
            st.update({"active": False, "current_score": 0, "last_word": None, "last_user_id": None})

    async def _invalid(self, msg, woord, reason):
        st = self._get_state(msg.guild.id)
        if st["current_score"] > st["high_score"]:
            st["high_score"] = st["current_score"]
        st.update({"current_score": 0, "last_word": None, "last_user_id": None})
        await self._assign_task(msg.guild.id, msg.author, woord, reason)

    async def _assign_task(self, gid, user, woord, reason):
        st = self._get_state(gid)
        combined = self.tasks_data["default_tasks"] + self._guild_tasks(gid)
        taak = random.choice(combined) if combined else "Geen taak beschikbaar."
        timeout = st.get("task_timeout") or 180
        st["paused"] = True
        st["current_task_user_id"] = user.id
        st["task_expires_at"] = time.time() + timeout
        self.games[gid] = st
        self._save_state()
        # schedule timeout task (cancel previous if exists)
        t = self._timeout_tasks.get(gid)
        if t and not t.done(): t.cancel()
        self._timeout_tasks[gid] = asyncio.create_task(self._wait_timeout(gid, timeout))

        tc = st.get("task_channel_id") or self._guild_task_channel(gid)

        game_ch = self.bot.get_channel(st["channel_id"])
        task_ch = self.bot.get_channel(tc)
        # bericht in spelkanaal met verwijzing naar taak-kanaal (indien ingesteld)
        if task_ch:
            task_channel_mention = task_ch.mention
            game_desc = (f"{user.mention} typte `{woord}` dat {reason}.\n\n"
                         f"De toegewezen taak staat in {task_channel_mention} en moet door {user.mention} uitgevoerd worden.\n"
                         f"**Taak:** {taak}\n⏱ Timeout: {timeout}s")
        else:
            game_desc = (f"{user.mention} typte `{woord}` dat {reason}.\n\n"
                         f"**Taak:** {taak}\n⏱ Timeout: {timeout}s\n\n"
                         "⚠️ Er is geen taak-kanaal ingesteld; gebruik `[p]ws settaskchannel #kanaal`.")
        await game_ch.send(embed=self.make_embed(title="🔁 Fout woord!", description=game_desc))

        # bericht in taak-kanaal met ping naar wie de taak moet uitvoeren
        if task_ch:
            await task_ch.send(embed=self.make_embed(
                title="📌 Nieuwe taak – actie vereist",
                description=f"{user.mention}, voer deze taak uit:\n\n{taak}\n\n"
                            "Wanneer je klaar bent, typ iets in dit kanaal om te bevestigen."
            ))

    async def _wait_timeout(self, gid, timeout):
        try:
            await asyncio.sleep(timeout)
            await self._task_completed(gid, False)
        except asyncio.CancelledError:
            pass

    async def _task_completed(self, gid, success, msg=None):
        st = self._get_state(gid)
        # determine channels
        game_ch = self.bot.get_channel(st.get("channel_id"))
        task_ch = self.bot.get_channel(st.get("task_channel_id"))
        # clear persisted task info
        st["paused"] = False
        st["current_task_user_id"] = None
        st.pop("task_expires_at", None)
        self.games[gid] = st
        self._save_state()
        # cancel any pending task
        t = self._timeout_tasks.get(gid)
        if t and not t.done():
            t.cancel()

        if success:
            actor_mention = msg.author.mention if msg and hasattr(msg, "author") else "De speler"
            last_word = st.get("last_word") or "geen vorig woord"
            # notify in task channel that task is completed and where the game continues
            if task_ch:
                try:
                    await task_ch.send(embed=self.make_embed(
                        title="✅ Taak voltooid",
                        description=(f"{actor_mention} heeft de taak voltooid. Het spel wordt hervat in {game_ch.mention if game_ch else 'het spelkanaal'}.")
                    ))
                except Exception:
                    pass
            # notify in game channel that the task was completed and show last word
            if game_ch:
                try:
                    await game_ch.send(embed=self.make_embed(
                        title="✅ Taak voltooid!",
                        description=(f"{actor_mention} heeft bevestigd dat de taak is uitgevoerd. Het spel wordt hervat.\n\n"
                                     f"Laatste woord: `{last_word}`")
                    ))
                except Exception:
                    pass
        else:
            # timeout / not completed
            if task_ch:
                try:
                    await task_ch.send(embed=self.make_embed(
                        title="⌛ Taak verlopen",
                        description="De toegewezen taak is niet binnen de gestelde tijd uitgevoerd. Het spel wordt hervat."
                    ))
                except Exception:
                    pass
            if game_ch:
                try:
                    await game_ch.send(embed=self.make_embed(
                        title="⌛ Timeout",
                        description="Niemand heeft gepost, het spel gaat verder."
                    ))
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(WoordspelTD(bot))
