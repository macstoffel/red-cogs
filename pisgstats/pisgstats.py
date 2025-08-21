
import discord, re, random, datetime
from redbot.core import commands, Config
from collections import defaultdict, Counter

WORD_RE = re.compile(r"[\w']+")
EMOJI_RE = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
LINK_RE = re.compile(r"https?://\S+")

STOPWORDS = {"de","het","een","en","ik","jij","je","u","we","wij","ze","zij","hun","hem","haar","die","dat","dit","is","was","te","van","voor","op","in","aan","om","met","maar","als","dan","ook","niet","wel","wat","hoe","waar","waarom","wanneer","dus","toen","al","nog","meer","minder"}

def tokenize(text): return [w.lower() for w in WORD_RE.findall(text)]
def extract_emojis(text): return EMOJI_RE.findall(text)

def svg_bar_chart(data, width=400, height=200, bar_color="#69c"):
    if not data: return ""
    max_val = max(data.values())
    step = width/len(data)
    svg = [f"<svg width='{width}' height='{height}'>"]
    for i,(label,val) in enumerate(data.items()):
        h = (val/max_val)*(height-20) if max_val>0 else 0
        x = i*step+5
        y = height-h-15
        svg.append(f"<rect x='{x}' y='{y}' width='{step-10}' height='{h}' fill='{bar_color}' />")
        svg.append(f"<text x='{x+2}' y='{height-2}' font-size='10'>{label}</text>")
    svg.append("</svg>")
    return ''.join(svg)

class PisgStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(channels_include=[], channels_exclude=[], stats={})

    async def _update_stats_for_message(self, message: discord.Message):
        if message.author.bot: return
        guild = message.guild
        if not guild: return
        gid = str(guild.id)
        stats = await self.config.guild(guild).stats()
        uid = str(message.author.id)
        gstats = stats.get("global",{})
        gstats.setdefault("messages",0); gstats["messages"]+=1
        gstats.setdefault("words",0); gstats.setdefault("chars",0)
        gstats["words"] += len(tokenize(message.content))
        gstats["chars"] += len(message.content)
        gstats.setdefault("hour_hist",[0]*24)
        gstats["hour_hist"][message.created_at.hour]+=1
        gstats.setdefault("joins",0); gstats.setdefault("leaves",0)

        ustats = stats.get(uid,{})
        ustats["name"]=str(message.author)
        ustats.setdefault("messages",0); ustats["messages"]+=1
        ustats.setdefault("words",0); ustats["words"]+=len(tokenize(message.content))
        ustats.setdefault("chars",0); ustats["chars"]+=len(message.content)
        ustats.setdefault("links",0); ustats["links"]+=len(LINK_RE.findall(message.content))
        ustats.setdefault("emoji",Counter()); ustats["emoji"].update(extract_emojis(message.content))
        ustats.setdefault("hour_hist",[0]*24); ustats["hour_hist"][message.created_at.hour]+=1
        today = str(datetime.date.today())
        if ustats.get("quote_date")!=today and random.random()<0.05:
            ustats["quote"]=message.content[:200]
            ustats["quote_date"]=today

        for w in tokenize(message.content):
            if w not in STOPWORDS:
                gstats.setdefault("wordcount",Counter()); gstats["wordcount"][w]+=1

        stats["global"]=gstats; stats[uid]=ustats
        await self.config.guild(guild).stats.set(stats)

    @commands.Cog.listener()
    async def on_message(self, message): await self._update_stats_for_message(message)
    @commands.Cog.listener()
    async def on_member_join(self, member):
        stats=await self.config.guild(member.guild).stats(); g=stats.get("global",{})
        g.setdefault("joins",0); g["joins"]+=1; stats["global"]=g
        await self.config.guild(member.guild).stats.set(stats)
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        stats=await self.config.guild(member.guild).stats(); g=stats.get("global",{})
        g.setdefault("leaves",0); g["leaves"]+=1; stats["global"]=g
        await self.config.guild(member.guild).stats.set(stats)

    @commands.group()
    async def pstats(self, ctx): pass

    @pstats.command()
    async def show(self, ctx):
        stats=await self.config.guild(ctx.guild).stats()
        g=stats.get("global",{})
        await ctx.send(f"Berichten: {g.get('messages',0)} | Woorden: {g.get('words',0)} | Joins: {g.get('joins',0)} | Leaves: {g.get('leaves',0)}")

    @pstats.command()
    async def html(self, ctx):
        stats=await self.config.guild(ctx.guild).stats()
        g=stats.get("global",{}); users={k:v for k,v in stats.items() if k!="global"}
        html=["<html><head><style>body{font-family:sans-serif;} h2{background:#eef;padding:4px;} table{border-collapse:collapse;} td,th{border:1px solid #ccc;padding:4px;} tr:nth-child(even){background:#f9f9f9;}</style></head><body>"]
        html.append("<h1>Statistieken</h1>")
        html.append(f"<h2>Globaal</h2><p>Berichten: {g.get('messages',0)}<br>Woorden: {g.get('words',0)}<br>Joins: {g.get('joins',0)} | Leaves: {g.get('leaves',0)}</p>")
        if "hour_hist" in g:
            html.append("<h3>Activiteit per uur</h3>"+svg_bar_chart({str(i):v for i,v in enumerate(g['hour_hist'])}, bar_color="#69c"))
        if "wordcount" in g:
            top=dict(Counter(g["wordcount"]).most_common(10))
            html.append("<h3>Topwoorden</h3>"+svg_bar_chart(top, bar_color="#6c9"))
        html.append("<h2>Gebruikers</h2><table><tr><th>Naam</th><th>Berichten</th><th>Actiefste uur</th><th>Aantal woorden</th><th>Aantal karakters</th><th>Emoji's</th><th>Quote</th></tr>")
        for uid,u in users.items():
            besth=u.get("hour_hist",[0]*24)
            active_hour=besth.index(max(besth)) if besth else "?"
            html.append(f"<tr><td>{u.get('name')}</td><td>{u.get('messages',0)}</td><td>{active_hour}:00</td><td>{u.get('words')}</td><td>{u.get('chars')}</td><td>{u.get('emoji')}</td><td>{u.get('quote','')}</td></tr>")
        html.append("</table></body></html>")
        fn="/tmp/pstats.html"; open(fn,"w",encoding="utf-8").write(''.join(html))
        await ctx.send(file=discord.File(fn))
