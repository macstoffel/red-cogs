# LoggingCog

Een Redbot Cog die alle berichten, edits, deletes en member join/leave events logt naar logbestanden.

## Logformaat
- Alleen tijd, geen datum
- Tijd altijd tussen blokhaken `[08:12:32]`
- Gebruikersnamen altijd tussen `< >`

Voorbeeld:
[08:12:32] [MESSAGE] #general <MacStoffel>: Hallo wereld!
[08:15:01] [EDIT] #general <MacStoffel>: 'Hallo wereld!' -> 'Hallo allemaal!'
[08:20:44] [DELETE] #general <MacStoffel>: Hallo allemaal!
[08:22:10] [JOIN] <NieuweGebruiker> (1234567890)

markdown
Copy
Edit

## Functies
- Dagelijkse logbestanden (`YYYY-MM-DD.log`)
- Een doorlopend `history.log` bestand
- Logging van:
  - Berichten
  - Bewerken/verwijderen van berichten
  - Member joins en leaves
- Commando om **volledige historie** te loggen: `[p]logset harvesthistory`

## Installatie
1. Voeg je repo toe aan Redbot:
2. [p]repo add MacStoffel https://github.com/macstoffel/red-cogs
3. [p]cog install MacStoffel loggingcog
4. [p]load loggingcog

2. Controleer de instellingen:
[p]logset status

3. Pas naar wens aan.

## Config commando’s

- `[p]logset toggle` → logging aan/uit  
- `[p]logset path <map>` → stel logmap in  
- `[p]logset addchannel #kanaal` → voeg kanaal toe  
- `[p]logset removechannel #kanaal` → verwijder kanaal  
- `[p]logset clearchannels` → verwijder alle kanalen (logt niets)  
- `[p]logset allchannels` → logt alle kanalen  
- `[p]logset harvesthistory` → schrijf de volledige historie van de ingestelde kanalen weg  
- `[p]logset status` → toon instellingen  

## Data
Alle logs worden lokaal opgeslagen in de ingestelde map. Er worden geen gegevens gedeeld met derden.
