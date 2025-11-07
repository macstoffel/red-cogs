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

## Commando's & rechten
Let op: `[p]` is de bot-prefix; vervang indien anders. Sommige commando's zijn beperkt tot moderators of hoger.

- `[p]taak`  
  Geeft een random taak (embed). Iedereen kan dit gebruiken. Toewijzingen worden, indien geconfigureerd, gelogd.

- `[p]taakgui`  
  Opent de interactieve GUI-embed met knoppen. Veel interacties zijn ephemeral (zichtbaar alleen voor de gebruiker).

- Administratie (vereist moderator of hoger via cog-perms of Red admin):
  - `[p]taakadd <tekst>`  
 Voeg een taak toe (moderator of hoger).
  - `[p]taakremove <nummer>`  
 Verwijder een taak op nummer (moderator of hoger).
  - `[p]taaklist`  
 Toont de takenlijst in een embed (moderator of hoger).
  - `[p]taaklogset [#kanaal]`  
 Stel het logkanaal in voor taak-toewijzingen. Laat leeg om uit te schakelen. (administrator/manage_guild required)

- GUI-beheer (gebruikersinterface):
  - Knoppen voor toevoegen/verwijderen/list zijn beveiligd: alleen moderators of hoger kunnen deze acties uit voeren via de GUI; anderen krijgen een melding dat ze geen toegang hebben.

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

---

## Licentie
MIT License — vrij te gebruiken en te wijzigen. Voeg je eigen naam en licentie-informatie toe voordat je de repo publiek maakt.

---

## Veelvoorkomende problemen
- *Knoppen werken niet / bot reageert niet*: controleer dat de bot online is en dat `intents` en benodigde permissies zijn ingeschakeld. Red moet ook up-to-date zijn.
- *Taken verdwijnen*: taken worden opgeslagen in Red's Config; zorg dat je Red-config niet gewist wordt. `taken.json` is alleen de bron van standaards.

---
