
# PisgStats (Red-DiscordBot Cog)

Pisg-achtige statistieken voor Discord, met HTML-rapportage.

## Installatie

1. Kopieer deze map naar de cogs-folder van je Redbot, of installeer via een path repo.
2. Herstart/reaad je bot of gebruik `reload`.
3. Laad de cog:
   ```
   [p]load pisgstats
   ```

## Gebruik (belangrijkste commands)

- `pstats help` – toon help
- `pstats include #kanaal` – track expliciet
- `pstats exclude #kanaal` – sluit uit
- `pstats listchannels` – lijst met huidige tracking-instellingen
- `pstats harvest #kanaal 2000` – lees 2000 historische berichten
- `pstats show` – compacte stats in Discord
- `pstats html` – genereer een HTML-rapport en upload bestand

## Opslag

- Opslag via Redbot **Config** (JSON). Geen externe database nodig.
- Per guild worden aggregaties bewaard. De inhoud van een bericht wordt niet opgeslagen.

## Privacy

Zie `info.json` voor de end user data statement. Gebruik deze cog met respect voor de privacy van je gebruikers en volgens de regels van je server.

## Licentie

MIT
