# RandomTasks - Redbot Cog (GUI & Per-server taken)

**RandomTasks** is een Redbot-cog die per-server (guild) lijsten met taken beheert en gebruikers via een interactieve, paarse embed (knoppen) een willekeurige taak laat kiezen. Taken worden standaard geladen vanuit `taken.json`, maar iedere server bewaart zijn eigen taken in een aparte JSON in `guild_data/`.

---

## Belangrijkste wijzigingen (recent)
- Taken worden per guild in een eigen JSON-bestand bewaard: `guild_data/<guildid>_tasks.json`.
- Per-guild custom titel voor de GUI embed mogelijk (`[p]taaktitleset`).
- Persistent Views gebruikt zodat knoppen blijven werken na bot-restart.
- Alleen moderators of hoger zien knoppen voor beheer (taak toevoegen/verwijderen/lijst); normale gebruikers zien alleen de knop voor een Random Taak.
- Optionele logging per guild: stel met `[p]taaklogset #kanaal` een logkanaal in. Logbericht bevat wie welke taak kreeg (display name + id), taaktekst, kanaal en timestamp.
- Geen extra bevestiging meer in kanaal bij toewijzing; gebruiker krijgt zijn taak (ephemeral/embed) en er wordt stil gelogd indien ingesteld.

---

## Features
- Per-server (guild) takenlijsten, persistente opslag per guild.
- GUI-achtige embed met knoppen:
  - 🎲 Random Taak — iedereen.
  - ➕ Taak toevoegen — alleen moderators of hoger (zichtbaar alleen voor mods).
  - 🗑 Taak verwijderen — alleen moderators of hoger (zichtbaar alleen voor mods).
  - 📋 Takenlijst — alleen moderators of hoger (zichtbaar alleen voor mods).
- Tekstcommando’s voor admins/mods om snel te beheren.
- Logging: toewijzingen worden in het ingestelde logkanaal gelogd met gebruiker, taak, kanaal en tijd.
- Standaardtaken in `taken.json` (gebruikt als seed).
- Paarse, consistente embeds en ephemeral responses voor de GUI.

---

## Installatie (kort)
1. Voeg de repo toe aan Red en installeer de cog.
2. Laad de cog:
```
[p]load randomtasks
```

---

## Commando's & rechten
Let op: `[p]` is de bot-prefix; vervang indien anders.

Publieke commando's
- `[p]taak`  
  Geeft een random taak (embed). Iedereen kan dit gebruiken.

GUI
- `[p]taakgui`  
  Opent de interactieve GUI. Moderators zien alle knoppen; normale gebruikers zien enkel "Random Taak".

Moderatie / configuratie (moderator of hoger / manage_guild voor sommige commands)
- `[p]taakadd <tekst>`  
  Voeg snel een taak toe (moderator of hoger).
- `[p]taakremove <nummer>`  
  Verwijder een taak op nummer (moderator of hoger).
- `[p]taaklist`  
  Toont de takenlijst (moderator of hoger).
- `[p]taaklogset [#kanaal]`  
  Stel het logkanaal in voor taak-toewijzingen. Laat leeg om uit te schakelen.
- `[p]taaktitleset [titel tekst]`  
  Stel een custom titel voor de GUI embed per guild. Laat leeg om de standaardtitel te herstellen.

---

## Bestandslocaties / persistentie
- Globale standaards: `taken.json`
- Per-guild persistent tasks: `guild_data/<guildid>_tasks.json`
  - Deze bestanden worden automatisch aangemaakt en bijgewerkt bij bewerkingen.
- Config keys (per guild) bevatten: `log_channel_id`, `custom_title` (en worden gebruikt naast de per-guild JSON).

---

## Logging
- Stel het logkanaal in met `[p]taaklogset #kanaal`.
- Logs bevatten:
  - Gebruiker: display name + (id)
  - Taak: volledige taaktekst
  - Kanaal: waar de taak werd aangevraagd
  - Timestamp (UTC)
- Logging is best-effort; indien permissies ontbreken of kanaal verdwenen is, faalt logging stil.

---

## Gedragsnotities & tips
- Knoppen voor toevoegen/verwijderen/lijst zijn onzichtbaar voor normale gebruikers; dit voorkomt verwarring en verkleint misbruik.
- Random taak wordt als embed in het kanaal geplaatst (optioneel auto-delete na korte tijd) en moderators kunnen dit via logs terugzien.
- Voor herstel/migratie van data of bulk-export van guild files kun je admin-commands toevoegen; vraag ernaar als je dat wilt.

---

## Licentie
MIT License — vrij te gebruiken en te wijzigen. Voeg je eigen naam en licentie-informatie toe voordat je de repo publiek maakt.
