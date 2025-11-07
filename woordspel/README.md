# Woordspel

🎮 Een woordketting spel voor Discord, gemaakt als Redbot cog.

---

## ✅ Installatie (via Discord)

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

## Commando's

- `[p]start [doelpunten]` – Start het spel. Optioneel: doelpunten instellen (standaard 10).  
- `[p]stop` – Stop het spel.  
- `[p]totaal` – Toon de huidige score.  
- `[p]highscore` – Toon de hoogste behaalde score ooit. 
```
- [p]woordspel start [doelpunten] – Start het spel. Optioneel: doelpunten instellen (standaard 10).  
- [p]woordspel stop – Stop het spel.  
- [p]woordspel totaal – Toon de huidige score.
- [p]woordspel highscore – Toon de hoogste behaalde score ooit. 
- [p]woordspel help 

---

## Regels

- Typ een woord dat begint met de laatste letter van het vorige woord.  
- Je mag niet twee keer achter elkaar.  
- Typ geen meerdere woorden tegelijk.  
- Fout woord → score reset → nieuwe ronde begint.  

---

## Features

- Embed styling in paarse tinten.  
- Scoretracking en highscore.  
- Doelpunten instelbaar.  
- Alleen in het ingestelde kanaal actief.  