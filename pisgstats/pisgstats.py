import asyncio
import re
import math
import html
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
import random

import discord
from redbot.core import commands, Config, checks, data_manager

__all__ = ["PisgStats"]

# Basis NL/EN stopwoorden (compact, uitbreidbaar)
STOPWORDS = {
    "de","het","een","en","of","ik","jij","hij","zij","wij","jullie","ze","je","we","ze","is","ben","zijn","was","waren","op","in","aan","te","voor","met","maar","van","dat","die","dit","dan","als","ook","niet","wel","wat","wie","waar","hoe","er","naar","bij","uit","om",
    "the","and","a","to","of","in","for","on","with","that","this","is","are","was","were","it","as","at","be","by","from","or","an","not","but","so","do","does","did","you","i","he","she","we","they","them","me","my","your","our","their"
}

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # Misc symbols & pictographs, emoticons, transport, supplemental symbols
    "\U00002700-\U000027BF"  # Dingbats
    "\U00002600-\U000026FF"  # Misc symbols
    "]+",
    flags=re.UNICODE
)
CUSTOM_EMOJI_RE = re.compile(r"<a?:\w+:\d+>")
LINK_RE = re.compile(r"https?://\S+")
MENTION_RE = re.compile(r"<@!?\d+>|<@&\d+>|<#\d+>")

def tokenize(text: str):
    # Houd unicode letters/cijfers bij elkaar; splits op niet-woord tekens
    return re.findall(r"[^\W_]+", text.lower(), re.UNICODE)

def extract_emojis(text: str):
    return EMOJI_RE.findall(text) + CUSTOM_EMOJI_RE.findall(text)

def svg_bar_chart(title, data_pairs, width=700, height=260, margin_left=100, margin_right=40):
    """Maak een simpele horizontale bar chart (SVG) uit (label, value)-paren."""
    if not data_pairs:
        return f"<h3>{html.escape(title)}</h3><p>Geen data.</p>"
    labels, values = zip(*data_pairs)
    max_v = max(values) or 1
    bar_height = (height - 2 * margin_left) / len(values)
    svg = [f'<h3>{html.escape(title)}</h3>']
    svg.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append(f'<text x="{width/2}" y="20" text-anchor="middle" font-size="14">{html.escape(title)}</text>')
    for i, (lab, val) in enumerate(data_pairs):
        y = margin_left + i * bar_height
        w = (width - margin_left - margin_right) * (val / max_v)
        label_text = str(lab)
        if len(label_text) > 20:
            label_text = label_text[:17] + "..."
        svg.append(f'<rect x="{margin_left}" y="{y+4}" width="{w}" height="{bar_height-8}" fill="steelblue"/>')
        svg.append(f'<text x="{margin_left - 8}" y="{y+bar_height/2}" text-anchor="end" dominant-baseline="middle" font-size="12">{html.escape(label_text)}</text>')
        svg.append(f'<text x="{margin_left + w + 4}" y="{y+bar_height/2}" dominant-baseline="middle" font-size="12">{val}</text>')
    svg.append(f'<line x1="{margin_left}" y1="{height-margin_left}" x2="{width-margin_right}" y2="{height-margin_left}" stroke="black"/>')
    svg.append('</svg>')
    return "".join(svg)


def svg_bar_chart_vertical(title, data_pairs, width=700, height=260, margin=40, max_bars=24):
    """Verticale bar chart (SVG) – handig voor uren (0..23)."""
    if not data_pairs:
        return f"<h3>{html.escape(title)}</h3><p>Geen data.</p>"
    data_pairs = data_pairs[:max_bars]
    labels, values = zip(*data_pairs)
    max_v = max(values) or 1
    n = len(data_pairs)
    bar_w = (width - 2 * margin) / max(n, 1)
    svg = [f'<h3>{html.escape(title)}</h3>']
    svg.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append(f'<text x="{width/2}" y="20" text-anchor="middle" font-size="14">{html.escape(title)}</text>')
    for i, (lab, val) in enumerate(data_pairs):
        x = margin + i * bar_w
        h = (height - 2 * margin) * (val / max_v)
        y = height - margin - h
        svg.append(f'<rect x="{x+2}" y="{y}" width="{bar_w-4}" height="{h}" />')
        svg.append(f'<text x="{x+bar_w/2}" y="{height - margin + 12}" text-anchor="middle" font-size="10">{html.escape(str(lab))}</text>')
        svg.append(f'<text x="{x+bar_w/2}" y="{y-2}" text-anchor="middle" font-size="10">{val}</text>')
    svg.append(f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="black"/>')
    svg.append('</svg>')
    return "".join(svg)

class PisgStats(commands.Cog):
    """Pisg-achtige statistieken voor Discord, met HTML-rapport."""
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow().replace(tzinfo=timezone.utc)  # Toegevoegd
        self.config = Config.get_conf(self, identifier=0xBEEFCAFE1234, force_registration=True)
        default_guild = {
            "tracked_channels": [],
            "ignored_channels": [],
            "messages": 0,
            "characters": 0,
            "links": 0,
            "attachments": 0,
            "hour_hist": [0]*24,
            "day_hist": {},
            "words": {},
            "emojis": {},
            "channels": {},
            "users": {},
        }
        self.config.register_guild(**default_guild)

    # ---------- helpers ----------

    async def _is_tracked(self, guild, channel_id: int) -> bool:
        conf = await self.config.guild(guild).all()
        tracked = conf["tracked_channels"]
        ignored = conf["ignored_channels"]
        if channel_id in ignored:
            return False
        # als tracked leeg is -> alles tracken, anders alleen expliciet
        return (not tracked) or (channel_id in tracked)

    @staticmethod
    def _count_upper_ratio(text: str):
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        upp = sum(1 for c in letters if c.isupper())
        return upp / len(letters)

    def _update_stats_for_message(self, gconf: dict, message: discord.Message):
        content = message.content or ""
        words = tokenize(content)
        emojis = extract_emojis(content)
        links = LINK_RE.findall(content)
        mentions = MENTION_RE.findall(content)
        qmarks = content.count("?")
        excls = content.count("!")
        upp_ratio = self._count_upper_ratio(content)
        shouting = 1 if (upp_ratio >= 0.6 and len(content) >= 8) else 0
        chars = len(content)

        # globals
        gconf["messages"] += 1
        gconf["characters"] += chars
        gconf["links"] += len(links)
        gconf["attachments"] += len(message.attachments)
        # hour/day
        ts = message.created_at.astimezone(timezone.utc)
        gconf["hour_hist"][ts.hour] += 1
        day = ts.strftime("%Y-%m-%d")
        gconf["day_hist"][day] = gconf["day_hist"].get(day, 0) + 1

        # words (met stopwoordenfilter)
        for w in words:
            if w in STOPWORDS or len(w) <= 2:
                continue
            gconf["words"][w] = gconf["words"].get(w, 0) + 1

        # emojis
        for e in emojis:
            gconf["emojis"][e] = gconf["emojis"].get(e, 0) + 1

        # channel
        ch = gconf["channels"].setdefault(str(message.channel.id), {"messages":0,"words":0,"characters":0})
        ch["messages"] += 1
        ch["words"] += len(words)
        ch["characters"] += chars

        # user
        u = gconf["users"].setdefault(str(message.author.id), {
            "name": getattr(message.author, "display_name", str(message.author)),
            "messages":0,"words":0,"characters":0,
            "links":0,"attachments":0,"mentions":0,
            "questions":0,"exclaims":0,"emoji":0,
            "shouts":0,"longest":0,"avg_upper":0.0,
            "quotes": []
        })
        u["name"] = getattr(message.author, "display_name", u["name"])
        u["messages"] += 1
        u["words"] += len(words)
        u["characters"] += chars
        u["links"] += len(links)
        u["attachments"] += len(message.attachments)
        u["mentions"] += len(mentions)
        u["questions"] += (1 if qmarks > 0 else 0)
        u["exclaims"] += (1 if excls > 0 else 0)
        u["emoji"] += len(emojis)
        u["shouts"] += shouting
        u["longest"] = max(u["longest"], chars)
        # eenvoudige lopende gemiddelde voor uppercase-ratio
        # avg = avg + (new-avg)/n
        n = u["messages"]
        u["avg_upper"] = u["avg_upper"] + (upp_ratio - u["avg_upper"]) / max(n, 1)

        # Quotes: bewaar recente berichten als mogelijke quotes (cap 10)
        qtext = content.strip()
        if qtext:
            qlist = u.setdefault("quotes", [])
            qlist.append(qtext)
            if len(qlist) > 10:
                # hou alleen de laatste 10
                del qlist[0:len(qlist)-10]

    # ---------- listeners ----------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if not await self._is_tracked(message.guild, message.channel.id):
            return
        async with self.config.guild(message.guild).all() as gconf:
            self._update_stats_for_message(gconf, message)

    # ---------- commands ----------

    @commands.group(name="pstats", invoke_without_command=True)
    @commands.guild_only()
    async def pstats(self, ctx: commands.Context):
        """Pisg-achtige statistieken en HTML-rapportage."""
        await ctx.send_help()

    @pstats.command(name="help")
    async def pstats_help(self, ctx: commands.Context):
        await ctx.send(
            "Commands: include, exclude, listchannels, harvest, reset, show, html\n"
            "**Voorbeeld:** `[p]pstats harvest #general 2000`"
        )

    @checks.admin_or_permissions(manage_guild=True)
    @pstats.command(name="include")
    async def pstats_include(self, ctx, channel: discord.TextChannel):
        """Track dit kanaal expliciet (leeg = alle kanalen)."""
        conf = self.config.guild(ctx.guild)
        tracked = await conf.tracked_channels()
        if channel.id not in tracked:
            tracked.append(channel.id)
            await conf.tracked_channels.set(tracked)
        await ctx.send(f"✅ Tracking ingeschakeld voor {channel.mention}")

    @checks.admin_or_permissions(manage_guild=True)
    @pstats.command(name="exclude")
    async def pstats_exclude(self, ctx, channel: discord.TextChannel):
        """Sluit dit kanaal uit van tracking."""
        conf = self.config.guild(ctx.guild)
        ignored = await conf.ignored_channels()
        if channel.id not in ignored:
            ignored.append(channel.id)
            await conf.ignored_channels.set(ignored)
        await ctx.send(f"🚫 {channel.mention} uitgesloten van tracking.")

    @pstats.command(name="listchannels")
    async def pstats_listchannels(self, ctx):
        conf = await self.config.guild(ctx.guild).all()
        tracked = conf["tracked_channels"]
        ignored = conf["ignored_channels"]
        def fmt(ids):
            if not ids: return "—"
            return ", ".join(f"<#{i}>" for i in ids)
        await ctx.send(
            f"**Tracked:** {fmt(tracked)}\n"
            f"**Ignored:** {fmt(ignored)}"
        )

    @checks.admin_or_permissions(manage_guild=True)
    @pstats.command(name="harvest")
    async def pstats_harvest(self, ctx, channel: discord.TextChannel, limit: int = 1000):
        """Lees historische berichten in (tot LIMIT)."""
        await ctx.typing()
        n = 0
        async with self.config.guild(ctx.guild).all() as gconf:
            async for msg in channel.history(limit=limit, oldest_first=True):
                if msg.author.bot:
                    continue
                if not await self._is_tracked(ctx.guild, channel.id):
                    continue
                self._update_stats_for_message(gconf, msg)
                n += 1
        await ctx.send(f"📥 Klaar: {n} berichten verwerkt uit {channel.mention}.")

    @checks.admin_or_permissions(manage_guild=True)
    @pstats.command(name="reset", confirmation=True)
    async def pstats_reset(self, ctx):
        """Wis alle statistieken (gild-niveau)."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("♻️ Statistieken gereset.")

    @pstats.command(name="show")
    async def pstats_show(self, ctx):
        """Toon compacte top-lijsten in Discord."""
        conf = await self.config.guild(ctx.guild).all()
        users = conf["users"]
        channels = conf["channels"]
        words = conf["words"]
        emojis = conf["emojis"]
        top_users = sorted(users.items(), key=lambda kv: kv[1].get("messages", 0), reverse=True)[:10]
        top_channels = sorted(channels.items(), key=lambda kv: kv[1].get("messages", 0), reverse=True)[:10]
        top_words = sorted(words.items(), key=lambda kv: kv[1], reverse=True)[:10]
        top_emojis = sorted(emojis.items(), key=lambda kv: kv[1], reverse=True)[:10]

        def fmt_users(us):
            out = []
            for uid, u in us:
                member = ctx.guild.get_member(int(uid))
                name = member.display_name if member else u.get("name", uid)
                out.append(f"{name}: {u.get('messages',0)}")
            return "\n".join(out) or "—"

        emb = discord.Embed(title="Pisg-stats (compact)", colour=discord.Colour.blurple())
        emb.add_field(name="Top Gebruikers (berichten)", value=fmt_users(top_users), inline=False)
        emb.add_field(name="Top Kanalen (berichten)", value="\n".join(f"<#{cid}>: {c['messages']}" for cid, c in top_channels) or "—", inline=False)
        emb.add_field(name="Top Woorden", value="\n".join(f"{w}: {c}" for w, c in top_words) or "—", inline=False)
        emb.add_field(name="Top Emoji", value=" ".join(f"{e} ×{c}" for e, c in top_emojis) or "—", inline=False)
        emb.set_footer(text=f"Totaal: {conf['messages']} berichten, {conf['characters']} tekens")
        await ctx.send(embed=emb)

    @pstats.command(name="html")
    async def pstats_html(self, ctx):
        """Genereer HTML-rapport en upload als bestand."""
        conf = await self.config.guild(ctx.guild).all()
        guild = ctx.guild

        # Voeg deze toe:
        users = conf["users"]
        channels = conf["channels"]
        words = conf["words"]
        emojis = conf["emojis"]
        hour_hist = conf["hour_hist"]

        # Bereken runtime
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        runtime = now - self.start_time
        runtime_str = str(runtime).split('.')[0]  # zonder microseconden
        start_str = self.start_time.strftime('%Y-%m-%d %H:%M:%SZ')

        # Laatste 31 dagen berichten
        day_hist = conf["day_hist"]
        last_days = []
        for i in range(30, -1, -1):
            d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            last_days.append((d, day_hist.get(d, 0)))

        # Labels verkorten naar MM-DD
        short_days = [(d[5:], n) for d, n in last_days]

        # Maak bredere SVG-chart
        days_svg = svg_bar_chart_vertical("Berichten per dag (laatste 31 dagen)", short_days, width=1200, height=300, margin=60, max_bars=31)

        # Top lijsten
        top_users = sorted(users.items(), key=lambda kv: kv[1].get("messages", 0), reverse=True)[:20]
        top_channels = sorted(channels.items(), key=lambda kv: kv[1].get("messages", 0), reverse=True)[:20]
        top_words = sorted(words.items(), key=lambda kv: kv[1], reverse=True)[:50]
        top_emojis = sorted(emojis.items(), key=lambda kv: kv[1], reverse=True)[:30]

        # SVG charts
        hours_pairs = [(str(i), hour_hist[i]) for i in range(24)]
        hours_svg = svg_bar_chart_vertical("Actiefste uren (UTC)", hours_pairs)

        # Kanaalactiviteit grafiek verwijderd per verzoek

        # HTML opbouw
        def user_row(uid, u):
            member = guild.get_member(int(uid))
            name = html.escape(member.display_name if member else u.get("name", uid))
            # kies willekeurige quote indien aanwezig, anders streepje
            quotes = u.get("quotes") or []
            if quotes:
                quote = random.choice(quotes)
                # toon volledige quote, escape en behoud regelafbreking
                quote_html = html.escape(quote).replace("\n", "<br>")
            else:
                quote_html = "—"
            return (
                f"<tr><td>{name}</td>"
                f"<td>{u.get('messages',0)}</td>"
                f"<td>{u.get('words',0)}</td>"
                f"<td>{u.get('characters',0)}</td>"
                f"<td>{u.get('links',0)}</td>"
                f"<td>{u.get('emoji',0)}</td>"
                f"<td>{u.get('questions',0)}</td>"
                f"<td>{quote_html}</td>"
                f"</tr>"
            )

        css = """
        <style>
        :root{
          --bg:#0f1020;
          --panel:#141423;
          --muted:#9aa0c3;
          --accent:#8a5be0;
          --accent-2:#7c5cff;
          --text:#e8e8ff;
          --table-border: rgba(255,255,255,0.06);
        }
        html,body{height:100%;}
        body{
          background:linear-gradient(180deg,var(--bg), #0b0b12);
          color:var(--text);
          font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
          padding:24px;
          -webkit-font-smoothing:antialiased;
          line-height:1.5;
        }
        h1{margin:0 0 8px 0; color:var(--accent); font-weight:700; letter-spacing: -0.5px;}
        h2{margin-top:28px; color:var(--accent-2); border-bottom:1px solid rgba(124,92,255,0.08); padding-bottom:6px;}
        p{color:var(--muted);}
        table{border-collapse: collapse; width:100%; background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent); margin-top:12px; border-radius:8px; overflow:hidden;}
        th,td{border-bottom:1px solid var(--table-border); padding:10px 12px; font-size:13px; vertical-align:top;}
        th{background:rgba(255,255,255,0.02); color:var(--muted); text-transform:uppercase; font-weight:600; letter-spacing:0.6px; font-size:12px;}
        td{color:var(--text);}
        tr:hover td{background: linear-gradient(90deg, rgba(124,92,255,0.04), transparent);}
        .cols{display:grid; grid-template-columns: 1fr 1fr; gap:24px; align-items:start;}
        /* Quotes */
        td:nth-child(8) { white-space: pre-wrap; word-wrap: break-word; max-width: 60ch; color:var(--text); }
        /* SVG tweaks */
        svg rect { fill: var(--accent-2); rx:4; ry:4; }
        svg text { fill: var(--text); font-family: inherit; }
        /* small metadata */
        .meta{font-size:13px; color:var(--muted); margin-bottom:12px;}
        .badge{display:inline-block; background:rgba(138,91,224,0.12); color:var(--accent); padding:4px 8px; border-radius:999px; font-size:12px; margin-right:8px;}
        /* responsive */
        @media (max-width:900px){
          .cols{grid-template-columns: 1fr;}
          table, svg{width:100%;}
        }
        </style>
        """

        html_parts = [f"<!doctype html><html><head><meta charset='utf-8'><title>PisgStats - {html.escape(guild.name)}</title>{css}</head><body>"]
        html_parts.append(f"<h1>PisgStats – {html.escape(guild.name)}</h1>")
        html_parts.append(
            f"<p>Gegenereerd op {now.strftime('%Y-%m-%d %H:%M:%SZ')} • Cog gestart op <b>{start_str}</b> • Runtime: <b>{runtime_str}</b><br>"
            f"Totaal berichten: <b>{conf['messages']}</b> • Tekens: <b>{conf['characters']}</b> • Links: <b>{conf['links']}</b> • Bijlagen: <b>{conf['attachments']}</b></p>"
        )

        # Vervang de tabel door de SVG-chart
        html_parts.append(days_svg)

        # charts
        html_parts.append("<div class='cols'>")
        html_parts.append(hours_svg)
        html_parts.append("</div>")

        # top woorden
        html_parts.append("<h2>Meest gebruikte woorden</h2>")
        if top_words:
            html_parts.append("<table><tr><th>Woord</th><th>Aantal</th></tr>")
            for w, c in top_words:
                html_parts.append(f"<tr><td>{html.escape(w)}</td><td>{c}</td></tr>")
            html_parts.append("</table>")
        else:
            html_parts.append("<p>Geen data.</p>")

        # top emoji
        html_parts.append("<h2>Meest gebruikte emoji</h2>")
        if top_emojis:
            html_parts.append("<table><tr><th>Emoji</th><th>Aantal</th></tr>")
            for e, c in top_emojis:
                html_parts.append(f"<tr><td>{html.escape(e)}</td><td>{c}</td></tr>")
            html_parts.append("</table>")
        else:
            html_parts.append("<p>Geen data.</p>")

        # gebruikers tabel
        html_parts.append("<h2>Gebruikers</h2>")
        html_parts.append("<table><tr><th>Gebruiker</th><th>Berichten</th><th>Woorden</th><th>Tekens</th><th>Links</th><th>Emoji</th><th>Vragen</th><th>Random Quote</th></tr>")
        for uid, u in top_users:
            html_parts.append(user_row(uid, u))
        html_parts.append("</table>")

        html_parts.append("</body></html>")
        html_report = "".join(html_parts)

        # bestand maken en uploaden
        folder = data_manager.cog_data_path(self)
        outfile = folder / f"pisgstats_{ctx.guild.id}.html"
        try:
            outfile.write_text(html_report, encoding="utf-8")
        except Exception:
            # fallback
            with open(outfile, "w", encoding="utf-8") as f:
                f.write(html_report)

        await ctx.send(file=discord.File(str(outfile), filename=f"pisgstats_{ctx.guild.id}.html"))

    @pstats.command(name="quotes")
    async def pstats_quotes(self, ctx, member: discord.Member = None):
        """Toon opgeslagen quotes voor een gebruiker (debug)."""
        conf = await self.config.guild(ctx.guild).all()
        users = conf.get("users", {})
        target = member or ctx.author
        u = users.get(str(target.id))
        if not u:
            return await ctx.send(f"Geen data voor {target.display_name}.")
        quotes = u.get("quotes", []) or []
        if not quotes:
            return await ctx.send(f"Geen quotes gevonden voor {target.display_name}.")
        # laat maximaal 20 quotes zien
        out_lines = [f"{i+1}. {q}" for i, q in enumerate(quotes[-20:])]
        # verstuur als codeblock om formatting te behouden
        await ctx.send(f"Quotes voor **{target.display_name}**:\n" + "```" + "\n".join(out_lines) + "```")
