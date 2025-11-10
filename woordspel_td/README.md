# Woordspel_TD v2.1

Een uitgebreid Nederlandstalig woordketting-spel voor Discord, met:
✅ JSON-opslag  
✅ Leaderboard  
✅ Taken bij fouten  
✅ Automatische cooldown  
✅ Strafpunten  
✅ Woordhistorie (wie gebruikte welk woord)

---

## ✅ Installatie

1) **Voeg de repo toe aan Redbot**
   Typ in een kanaal waar je bot toegang heeft (met jouw adminrechten):

   ```
   [p]repo add MacStoffel https://github.com/MacStoffel/redcogs
   ```

2) **Installeer de cog**
   ```
   [p]cog install MacStoffel woordspel
   ```

3) **Laad de cog**
   ```
   [p]load woordspel
   ```
---

## ✅ Nieuwe functies

### ✅ Leaderboard
- Iedere gebruiker die een geldig woord typt, verdient 1 punt
- Fout woord = -1 punt
- Eigen score bekijken:
```
[p]woordspel_td myscore
```
- Leaderboard top 10:
```
[p]woordspel_td leaderboard
```

### ✅ Taken & Cooldown
- Gebruik `[p]woordspel_td settaskchannel #kanaal` om het taak-kanaal in te stellen
- Bij verkeerd woord:
  ✅ Spel pauzeert  
  ✅ Speler krijgt een taak uit tasks.json  
  ✅ Speler moet taak uitvoeren in het taak-kanaal  
  ✅ Bot controleert automatisch  
  ✅ Spel gaat verder

---

## ✅ Commands

| Command | Functie |
|--------|---------|
| `[p]woordspel_td start [score]` | Start spel |
| `[p]woordspel_td stop` | Stop spel |
| `[p]woordspel_td total` | Toon huidige score |
| `[p]woordspel_td used <woord>` | Bekijk wie een woord eerder gebruikte |
| `[p]woordspel_td task` | Krijg een willekeurige taak |
| `[p]woordspel_td addtask <tekst>` | Voeg taak toe (met veiligheid-check) |
| `[p]woordspel_td listtasks` | Toon alle taken |
| `[p]woordspel_td settaskchannel #kanaal` | Stel verplicht taak-kanaal in |
| `[p]woordspel_td myscore` | Toon eigen punten |
| `[p]woordspel_td leaderboard` | Toon top 10 spelers |

---

## ✅ Veiligheid en Toegestane taken

✅ Speels, suggestief, humoristisch  
✅ Verhalen of opdrachten rond speelgoed, rollenspel, situaties  
❌ Geen echte personen  
❌ Geen expliciete porno  
❌ Geen verzoek om foto’s van personen  
❌ Geen persoonlijke gegevens

Bot controleert dit automatisch bij `[p]woordspel_td addtask`

---

## ✅ Data bestanden

| Bestand | Functie |
|---------|---------|
| `words.json` | Welke woorden zijn gebruikt en door wie |
| `tasks.json` | Takenlijst |
| `leaderboard.json` | Punten per gebruiker |
| `settings.json` | Opslag taak-kanaal per guild |

---

## ✅ Verwijderen & Reset

Wil je alles resetten?
1. Stop spel: `[p]woordspel_td stop`
2. Verwijder JSON-bestanden in `/data`


## Dependancies

- sudo apt install enchant-2
- sudo apt install myspell-nl
- pip install pyenchant (beware of the venv you're in)