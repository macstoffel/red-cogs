# Woordspel_TD v2.1

Een uitgebreid Nederlandstalig woordketting-spel voor Discord, met:
✅ JSON-opslag  
✅ Leaderboard  
✅ Taken bij fouten (met taak-kanaal & automatische controle)  
✅ Automatische cooldown / pauze bij fouten  
✅ Strafpunten  
✅ Woordhistorie (wie gebruikte welk woord)  
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

## Wat is nieuw in deze versie
- Als een speler een ongeldig woord typt (of met de verkeerde beginletter), pauzeert het spel automatisch en krijgt die speler een taak toegewezen.
- De taak wordt in een apart, ingesteld taak-kanaal geplaatst en de speler wordt daar gepingt.
- Het spel blijft gepauzeerd totdat de toegewezen speler bevestigt in het taak-kanaal (typ iets) dat de taak is uitgevoerd.
- Zodra de taak is uitgevoerd, meldt de bot in het spelkanaal het laatste woord en dat het spel hervat kan worden.
- Als het spel gepauzeerd is en iemand tóch een woord typt in het spelkanaal, wordt dat bericht verwijderd en krijgt die persoon een korte waarschuwing (auto-delete na 5s).
- Alle belangrijke meldingen zijn in paarse embeds voor consistente styling.
- Timeouts en best-effort checks: als taak niet binnen 5 minuten wordt uitgevoerd, wordt het spel hervat en wordt dit gemeld.

---

## Belangrijke commands (gebruik `[p]` als prefix)

Spelbeheer
- `[p]woordspel_td start [doelpunten]`  
  Start het spel in het huidige kanaal (per guild). Optioneel doelpunten meegeven.
- `[p]woordspel_td stop`  
  Stop het spel.
- `[p]woordspel_td total`  
  Toon huidige score voor de lopende sessie.
- `[p]woordspel_td myscore`  
  Toon je persoonlijke score (leaderboard).
- `[p]woordspel_td leaderboard`  
  Top 10 scores.

Woorden & controle
- `[p]woordspel_td used <woord>`  
  Toon wie een woord eerder gebruikte.

Taken & instellingen
- `[p]woordspel_td task`  
  Toon een willekeurige taak (helpful, debugging).
- `[p]woordspel_td addtask <tekst>`  
  Voeg een taak toe. De cog filtert expliciete items (geen echte personen/naakt/porno e.d.).
- `[p]woordspel_td listtasks`  
  Toon alle taken (genummerd).
- `[p]woordspel_td settaskchannel #kanaal`  
  (Mod/admin) Stel het kanaal in waar taken uitgevoerd en gecontroleerd worden. Zonder task-kanaal werkt de taakflow niet.

Debug / beheer
- JSON-bestanden (per repo) bijhouden: words.json, tasks.json, leaderboard.json, settings.json

---

## Gedrag bij fouten / taak-flow (stap-voor-stap)
1. Speler X typt een ongeldig woord of begint met de verkeerde letter.
2. Bot pauzeert het spel en wijst speler X een taak toe.
3. Bot post in het ingestelde taak-kanaal een embed met de taak en mention naar speler X:  
   "{player.mention}, voer deze taak uit: <taaktekst> — reageer in dit kanaal wanneer voltooid."
4. In het spelkanaal verschijnt een korte melding dat het spel gepauzeerd is en wie de taak moet uitvoeren.
5. Indien iemand in het spelkanaal probeert te spelen tijdens pauze: het bericht wordt verwijderd en er verschijnt een korte waarschuwing (verwijdert na 5s).
6. Zodra speler X iets typt in het taak-kanaal (of binnen 5 minuten bevestigt),:
   - Bot stuurt in het taak-kanaal: "✅ Taak voldaan — {player.mention}"
   - Bot stuurt in het spelkanaal: "✅ Taak uitgevoerd door {player.mention}. Laatste woord was: `<laatste woord>`. Spel kan verdergaan."
7. Als speler X niet binnen 5 minuten bevestigt, wordt het spel hervat en wordt dit gemeld.

---

## Data bestanden (locatie: `data/` in de cog-map)
- `words.json` — welke woorden zijn gebruikt en door wie
- `tasks.json` — takenlijst (array van objecten met id, text, added_by)
- `leaderboard.json` — punten per gebruiker
- `settings.json` — per-guild instellingen (zoals task_channel)

---

## Veiligheid en moderatie
- Taaktoevoeging bevat filtering op expliciete inhoud; content met echte personen/foto-verzoeken wordt geweigerd.
- Alleen moderators kunnen het taak-kanaal instellen (`settaskchannel` vereist mod/admin perms).
- Zorg dat de bot permissies heeft om berichten te sturen en te verwijderen in zowel spel- als taak-kanaal.

---

## Tips & veelvoorkomende issues
- Stel altijd eerst het taak-kanaal in met `[p]woordspel_td settaskchannel #kanaal`. Zonder dit werkt de pauze/taak flow niet.
- Controleer dat pyenchant en de Nederlandse dictionary geïnstalleerd zijn (zie hieronder).
- Als de bot geen berichten kan posten in het taak-kanaal, wordt de taak-flow afgebroken en krijgt de server een melding om permissies te controleren.

---

## Dependencies
- enchant / pyenchant + Nederlandse dictionary:
  - Debian/Ubuntu:
    ```
    sudo apt install enchant-2 myspell-nl
    pip install pyenchant
    ```
  - Zorg dat je in de juiste virtualenv/container installeert.

---

## Reset & backup
- Stop het spel: `[p]woordspel_td stop`
- Verwijder of backup JSON-bestanden in `data/` als je alles wilt resetten.

---

## Licentie
MIT License — vrij te gebruiken en te wijzigen. Pas aan naar wens voordat je publiek publiceert.

---