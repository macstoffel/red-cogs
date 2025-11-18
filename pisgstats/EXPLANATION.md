
# Uitleg: `pisgstats.py` (Redbot Cog)

Deze cog probeert de klassieke **pisg**-statistieken voor IRC te benaderen, maar dan voor **Discord**.
Alle opslag gebeurt via **Redbot Config** (JSON op schijf), dus geen database nodig.

## Hoe het werkt

- De cog luistert naar `on_message` en telt per bericht verschillende kenmerken:
  - gebruiker, kanaal, tijd (uur/dag)
  - woorden, tekens, hoofdletterratio (detectie van "shouting")
  - vraag-/uitroeptekens, links, emoji (standaard + custom), mentions, bijlagen
- Het bewaart samengevatte statistieken per **guild**, **gebruiker** en **kanaal** in `Config`.
- Je kunt optioneel historische berichten inlezen met `pstats harvest` (per kanaal).

### Belangrijkste datastructuur (per guild)

```python
{
  "tracked_channels": [],          # lijst van channel-ids; leeg == alle tekstkanalen tracken
  "ignored_channels": [],          # lijst van uitgesloten channels
  "messages": 0,                   # totaal aantal berichten
  "characters": 0,                 # totaal aantal tekens
  "links": 0,                      # totaal aantal links
  "attachments": 0,                # totaal aantal bijlagen
  "hour_hist": [0]*24,             # verdeling per uur
  "day_hist": {"YYYY-MM-DD": n},   # verdeling per dag
  "words": {"woord": n, ...},      # globale woordfrequentie
  "emojis": {"😀": n, ...},        # globale emoji-frequentie
  "channels": {
    str(channel_id): {"messages": n, "words": n, "characters": n}
  },
  "users": {
    str(user_id): {
      "name": "Displaynaam laatst gezien",
      "messages": n, "words": n, "characters": n,
      "links": n, "attachments": n, "mentions": n,
      "questions": n, "exclaims": n, "emoji": n,
      "shouts": n, "longest": 0, "avg_upper": 0.0
    }
  }
}
```

> Let op: Inhoud van berichten wordt **niet** volledig opgeslagen; enkel tellingen en beperkte aggregaties.

## HTML-rapport

- `pstats html` bouwt één HTML-bestand met:
  - samenvatting (totaal, topgebruikers, topkanalen)
  - bar-charts (SVG) voor **actiefste uren** en **kanaalactiviteit**
  - lijsten met **meest gebruikte woorden**, **emoji**, **links/posters**
  - gebruikersprofielen (korte tabel met kerncijfers)
- Alle grafieken zijn **inline SVG**, dus geen externe libs of styles nodig.
- Het resultaat kan direct in Discord worden geüpload of op een webserver geplaatst worden.

## Commands (kort)

- `[p]pstats help` – overzicht
- `[p]pstats include #kanaal` – track een kanaal expliciet
- `[p]pstats exclude #kanaal` – sluit een kanaal uit
- `[p]pstats listchannels` – toon welke kanalen je trackt
- `[p]pstats harvest #kanaal [limiet=1000]` – lees historie in
- `[p]pstats reset` – wis alle stats (confirmation nodig)
- `[p]pstats show` – toon top-lijsten in Discord (embed)
- `[p]pstats html` – genereer HTML en upload als bestand

## Aanpasbare onderdelen

- **Stopwoorden** (NL/EN) in de variabele `STOPWORDS`.
- **Emoji-detectie** via regex-ranges; wil je nauwkeuriger, installeer evt. de `emoji`-lib en vervang `extract_emojis`.
- **SVG-styling** – pas gerust padding/lettertype/groottes aan in de functies `svg_bar_chart_*`.

## Beperkingen t.o.v. pisg

- Alleen berichten die aanwezig zijn (live of via `harvest`) worden meegeteld; geen retro-logs.
- Sommige "IRC-specifieke" dingen (zoals *actions* /me) zijn minder relevant; we tellen wel uitroepen/vragen/SHOUT.
- Geen weergave van topic/joins/quits (Discord heeft een ander model).

Veel plezier! 🎉
