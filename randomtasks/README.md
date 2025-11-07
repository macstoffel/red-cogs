# RandomTasks - Redbot Cog (GUI & Per-server taken)

**RandomTasks** is een Redbot-cog die per-server (guild) lijsten met taken beheert en gebruikers via een interactieve, paarse embed (knoppen) een willekeurige taak laat kiezen. Taken worden standaard geladen vanuit `taken.json`, maar iedere server heeft z'n eigen lijst in Redbot's Config.

---

## Features
- Per-server (guild) takenlijsten.
- GUI-achtige embed met knoppen:
  - 🎲 Random Taak (ephemeral) — iedereen kan een taak opvragen.
  - ➕ Taak toevoegen — alleen moderators of hoger.
  - 🗑 Taak verwijderen — alleen moderators of hoger.
  - 📋 Takenlijst — alleen moderators of hoger.
- Beheerbare taken via zowel GUI als tekstcommando's.
- Logging: moderator kan een logkanaal instellen; toewijzingen worden daar gelogd (wie welke taak kreeg, vanuit welk kanaal, timestamp).
- Standaardtaken in `taken.json`.
- Paarse embeds voor stijlconsistentie.

---

## Vereisten
- Red-DiscordBot (Red) — compatibel met recente versies.
- Python 3.8+
- Bot heeft benodigde intents & permissies (send messages, embed links, use interactions).

---

## Installatie (kort)
1. Voeg de repo toe aan Red:
```
[p]repo add MacStoffel https://github.com/MacStoffel/redcogs
```
2. Installeer de cog:
```
[p]cog install MacStoffel randomtasks
```
3. Laad de cog:
```
[p]load randomtasks
```

---

## Commando's
> Let op: standaard prefix van Red is `[p]`. Vervang dit door jouw prefix indien anders.

- `[p]taak`  
  Geeft een random taak voor de server (embed).

- `[p]taakgui`  
  Opent de interactieve GUI-embed met knoppen. Knoppen sturen veel reacties als **ephemeral** — alleen zichtbaar voor de gebruiker die ermee interageert.

- Beheer (vereist administrator-permissies in de code; Red's permission system regelt toegang):
  - Via de GUI: gebruik de ➕ en 🗑 knoppen om taken toe te voegen of te verwijderen.
  - De GUI vraagt je om invoer in het kanaal wanneer nodig (voor toevoegen/verwijderen).

---

## taken.json
`taken.json` bevat een object met een `tasks`-array:

```json
{
  "tasks": [
    "Drink een glas water",
    "Doe 10 push-ups",
    "Neem 2 minuten pauze",
    "Stuur iemand een compliment"
  ]
}
```

Bij eerste keer gebruik krijgt een server de standaardtaken toegewezen als er nog geen server-specifieke taken aanwezig zijn in Config.

---

## Opmerkingen & tips
- De GUI maakt gebruik van `discord.ui.View` en ephemeral responses zodat interacties niet het kanaal vervuilen.
- Als je de cog verder wilt uitbreiden kun je overwegen:
  - Slash commands (voor betere integratie)
  - Tijd-gestuurde dagelijkse taken (background task per guild)
  - Rechten per role (wie taken mag toevoegen/verwijderen)
  - Opslaan van taken in een aparte JSON per guild (momenteel gebruikt de cog Red's Config)

---

## Licentie
MIT License — vrij te gebruiken en te wijzigen. Voeg je eigen naam en licentie-informatie toe voordat je de repo publiek maakt.

---

## Veelvoorkomende problemen
- *Knoppen werken niet / bot reageert niet*: controleer dat de bot online is en dat `intents` en benodigde permissies zijn ingeschakeld. Red moet ook up-to-date zijn.
- *Taken verdwijnen*: taken worden opgeslagen in Red's Config; zorg dat je Red-config niet gewist wordt. `taken.json` is alleen de bron van standaards.

---
