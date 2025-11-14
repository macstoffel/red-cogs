# WoordspelV2 — Redbot Cog

WoordspelV2 is een uitgebreide en moderne versie van het klassieke woordketting-spel, volledig gebouwd voor Redbot.  
De cog bevat Nederlandse woordcontrole, taken bij foute woorden, pauzefuncties, time-outs, en uitgebreide configuratie.

Alle commands beginnen met **$ws**.

---

## ✨ Features

### ✔ Woordketting spel (Nederlands)
- Woorden moeten beginnen met de laatste letter van het vorige woord
- Slechts één woord toegestaan
- Gebruiker mag niet twee keer achter elkaar
- Controle via *pyenchant* Nederlandse woordenlijst

### ✔ Pauzefunctie bij fout woord
Kiest een speler een fout woord, dan:
- Het spel pauzeert
- In het spelkanaal verschijnt een melding
- De speler krijgt een “taak” in het takenkanaal
- Pas na het uitvoeren van de taak gaat het spel verder

### ✔ Taken-systeem (met JSON opslag)
- Alle taken worden opgeslagen in `tasks.json`
- Taken worden willekeurig gekozen
- Commands om taken toe te voegen of te verwijderen:
  - `$ws addtask "<taak>"`
  - `$ws removetask <id>`
  - `$ws listtasks`

### ✔ Time-out systeem
- Standaard 5 minuten
- Met commando instelbaar:
  - `$ws timeout <seconden>`

### ✔ Configureerbaar takenkanaal
- Stel zelf het kanaal in met:
  - `$ws taskchannel #kanaalnaam`

### ✔ Mooie paarse embeds
Alle berichten van het spel worden automatisch in paarse embeds weergegeven.

---

## 📥 Installatie

### 1. Voeg de repo toe aan je Redbot:

 [p]repo add MacStoffel https://github.com/MacStoffel/redcogs

### 2. Installeer de cog:

 [p] cog install MacStoffel woordspelv2

### 3. Laad de cog:

 [p] load woordspelv2


---

## 🎮 Commands

### Spelcommando’s
| Command | Functie |
|--------|---------|
| `$ws start [doelpunten]` | Start een nieuwe sessie |
| `$ws stop` | Stopt het spel |
| `$ws totaal` | Huidige score |
| `$ws highscore` | Hoogste score |
| `$ws help` | Overzicht embeds |

### Taakbeheer
| Command | Functie |
|--------|---------|
| `$ws addtask "<tekst>"` | Voegt een taak toe aan tasks.json |
| `$ws removetask <id>` | Verwijdert een taak |
| `$ws listtasks` | Bekijk alle taken |

### Configuratie
| Command | Functie |
|--------|---------|
| `$ws taskchannel #channel` | Stel takenkanaal in |
| `$ws timeout <seconden>` | Zet taak time-out |

---

## 📂 Bestandsstructuur

woordspelv2/
├── woordspelv2.py
├── init.py
├── info.json
├── README.md
└── tasks.json (automatisch aangemaakt)


---

## 🧩 Dependencies

- **pyenchant** (voor Nederlandse woordcontrole)  
Zorg dat de NL woordenlijst geïnstalleerd is.

---

## ❤️ Credits

Gemaakt voor een 18+ Nederlandse Discord community, met liefde.


