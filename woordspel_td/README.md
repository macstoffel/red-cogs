# Woordspel_TD v2.1

Een uitgebreid Nederlandstalig woordketting-spel voor Discord, met:
✅ JSON-opslag  
✅ Leaderboard  
✅ Taken bij fouten (met taak-kanaal & automatische controle)  
✅ Automatische cooldown / pauze bij fouten  
✅ Strafpunten  
✅ Paarse embeds en duidelijke gebruikersmeldingen

---
# filepath: /Users/krh0812/Documents/GitHub/red-cogs/woordspel_td/README.md

## ✅ Installatie

1) **Voeg de repo toe aan Redbot**
   ```
   [p]repo add MacStoffel https://github.com/MacStoffel/redcogs
   ```

2) **Installeer de cog**
   ```
   [p]cog install MacStoffel woordspel
   ```

3) **Laad de cog**
   ```
   [p]load woordspel_td
   ```

---

🎯 Spelcommando’s
Commando	Beschrijving
[p]ws start [doelpunten]	Start een nieuw spel.
[p]ws stop	Stopt het huidige spel.
[p]ws totaal	Toont huidige score.
[p]ws highscore	Toont hoogste score ooit.
🛠️ Beheer (alleen admin/mod)
Commando	Beschrijving
[p]ws settaskchannel #kanaal	Stel het kanaal in waar taken worden gepost.
[p]ws settimeout <seconden>	Stel de tijd in (default: 180 sec).
[p]ws addtask "tekst"	Voeg een extra taak toe voor deze guild.
[p]ws removetask <index>	Verwijder een taak uit de lijst.
[p]ws listtasks	Bekijk alle standaard- en guildtaken.
🧠 Spelregels

Slechts één woord per bericht.

Je mag niet twee keer achter elkaar.

Een woord moet beginnen met de laatste letter van het vorige.

Typ je een ongeldig woord → je krijgt een taak.

---

## Licentie
MIT License — vrij te gebruiken en te wijzigen. Pas aan naar wens voordat je publiek publiceert.

---