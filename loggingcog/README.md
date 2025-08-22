# LoggingCog

Een Redbot Cog die alle berichten, edits, deletes en member join/leave events logt naar logbestanden.

## Functies
- Dagelijkse logbestanden (`YYYY-MM-DD.log`)
- Een doorlopend `history.log` bestand
- Logging van:
  - Berichten
  - Bewerken/verwijderen van berichten
  - Member joins en leaves
- Config commando’s voor beheer:
  - `[p]logset toggle`
  - `[p]logset path <map>`
  - `[p]logset addchannel #kanaal`
  - `[p]logset removechannel #kanaal`
  - `[p]logset status`
  - `[p]logset harvesthistory`

## Installatie

1. Voeg je repo toe aan Redbot:
2. [p]repo add MacStoffel https://github.com/macstoffel/red-cogs
3. [p]cog install MacStoffel loggingcog
4. [p]load loggingcog

markdown
Copy
Edit

2. Controleer de instellingen:
[p]logset status

markdown
Copy
Edit

3. Pas naar wens aan.

## Data
Alle logs worden lokaal opgeslagen in de ingestelde map. Er worden geen gegevens gedeeld met derden.
