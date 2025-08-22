# LoggingCog

Een Redbot Cog die alle berichten, edits, deletes en member join/leave events logt naar **per-kanaal logbestanden** én één centraal logbestand.

## Logformaat
- Alleen tijd, geen datum
- Tijd altijd tussen blokhaken `[08:12:32]`
- Gebruikersnamen altijd tussen `< >`
- Kanaalnaam voorafgegaan door `#`

Voorbeeld:
```
[08:12:32] [MESSAGE] #general <MacStoffel> Hallo wereld!
[08:15:01] [EDIT] #general <MacStoffel> 'Hallo wereld!' -> 'Hallo allemaal!'
[08:20:44] [DELETE] #general <MacStoffel> Hallo allemaal!
[08:22:10] [JOIN] <NieuweGebruiker> (1234567890)
```

## Functies
- **Per-kanaal logbestanden** (bijv. `general.log`)
- **Centraal logbestand** (`all_channels.log`) met álle logging
- **Kanaalgeschiedenis harvesten**: per kanaal (`<kanaalnaam>_history.log`) of alle kanalen tegelijk
- Logging van:
  - Berichten
  - Bewerken/verwijderen van berichten
  - Member joins en leaves
- Commando om **volledige historie** te loggen: `[p]logset harvesthistory` (alle kanalen) of `[p]logset harvestchannel #kanaal` (één kanaal)

## Installatie
1. Voeg je repo toe aan Redbot:
   ```
   [p]repo add MacStoffel https://github.com/macstoffel/red-cogs
   [p]cog install MacStoffel loggingcog
   [p]load loggingcog
   ```
2. Controleer de instellingen:
   ```
   [p]logset status
   ```
3. Pas naar wens aan. De logging werkt bij start op alle kanalen!!
   ** !!Stel de map in voor de bestanden!! **

## Config commando’s

- `[p]logset toggle` → logging aan/uit  
- `[p]logset path <map>` → stel logmap in  
- `[p]logset addchannel #kanaal` → voeg kanaal toe  
- `[p]logset removechannel #kanaal` → verwijder kanaal  
- `[p]logset clearchannels` → verwijder alle kanalen (logt niets)  
- `[p]logset allchannels` → logt alle kanalen  
- `[p]logset harvesthistory` → schrijf de volledige historie van alle ingestelde kanalen weg  
- `[p]logset harvestchannel #kanaal` → schrijf de volledige historie van één kanaal weg  
- `[p]logset status` → toon instellingen  

## Data
Alle logs worden lokaal opgeslagen in de ingestelde map. Er worden geen gegevens gedeeld met derden.