# WoordspelV3 — Redbot Cog

WoordspelV3 is de vernieuwde, verbeterde en uitgebreidere versie van het Nederlandse woordketting‑spel voor Redbot.  
Deze versie bevat persistente scores, admin‑beheer, een optionele score‑behoud‑modus, en een verbeterd taak‑ en pauzesysteem.

Alle commands beginnen met **$ws3**.

---

## ✨ Features

### ✔ Woordketting spel (Nederlands)
- Woorden moeten beginnen met de laatste letter van het vorige woord
- Slechts één woord toegestaan
- Gebruiker mag niet twee keer achter elkaar
- Controle via *pyenchant* Nederlandse woordenlijst

### ✔ Pauzefunctie bij fout woord
Wanneer een speler een fout woord typt:
- Het spel pauzeert
- De speler krijgt een taak in het taak‑kanaal
- Het spel gaat pas verder wanneer de taak is uitgevoerd
- Of automatisch na een time‑out

### ✔ Taken-systeem (met JSON opslag)
- Taken worden opgeslagen in `tasks.json`
- Willekeurige taakselectie
- Commands om taken te beheren:
  - `$ws3 taakadd "<taak>"`
  - `$ws3 taakremove <id>`
  - `$ws3 taken`

### ✔ Time-out systeem
- Standaard 5 minuten
- Aanpasbaar via:
  - `$ws3 timeout <seconden>`

### ✔ Configureerbaar takenkanaal
- Stel zelf het kanaal in met:
  - `$ws3 taskchannel #kanaalnaam`

### ✔ Persistente score-opslag (NIEUW in V3)
- Score blijft bewaard bij een Redbot‑herstart
- Highscore blijft bewaard
- Laatste woord en doelpunten worden opgeslagen

### ✔ Admin scorebeheer (NIEUW in V3)
Beheerders kunnen nu:
- De score aanpassen:  
  `$ws3 setscore <waarde>`
- De highscore aanpassen:  
  `$ws3 sethighscore <waarde>`

### ✔ Optie: score behouden bij taak-succes (NIEUW in V3)
- Normaal wordt de score gereset bij een fout woord
- In V3 kun je instellen dat de score behouden blijft als de taak op tijd wordt uitgevoerd
- Aan/uit via:  
  `$ws3 keepscore true/false`

### ✔ Mooie paarse embeds
Alle spelberichten worden automatisch in paarse embeds weergegeven.

---

## 📥 Installatie

### 1. Voeg de repo toe aan je Redbot:

[p] repo add MacStoffel https://github.com/MacStoffel/redcogs


### 2. Installeer de cog:

[p] cog install MacStoffel woordspelv3


### 3. Laad de cog:

[p] load woordspelv3


---

## 🎮 Commands

### Spelcommando’s
| Command | Functie |
|--------|---------|
| `$ws3 start [doelpunten]` | Start een nieuwe sessie |
| `$ws3 stop` | Stopt het spel |
| `$ws3 totaal` | Huidige score |
| `$ws3 highscore` | Hoogste score |
| `$ws3 help` | Overzicht embeds |

### Taakbeheer
| Command | Functie |
|--------|---------|
| `$ws3 taakadd "<tekst>"` | Voegt een taak toe |
| `$ws3 taakremove <id>` | Verwijdert een taak |
| `$ws3 taken` | Bekijk alle taken |

### Configuratie
| Command | Functie |
|--------|---------|
| `$ws3 taskchannel #kanaal` | Stel takenkanaal in |
| `$ws3 timeout <seconden>` | Zet taak time-out |
| `$ws3 keepscore true/false` | Score behouden bij taak-succes |

### Admin scorebeheer (nieuw)
| Command | Functie |
|--------|---------|
| `$ws3 setscore <waarde>` | Pas de huidige score aan |
| `$ws3 sethighscore <waarde>` | Pas de highscore aan |

---

## 📂 Bestandsstructuur

woordspelv3/
├── woordspelv3.py
├── init.py
├── info.json
├── README.md
└── data/
└── tasks.json (automatisch aangemaakt)


---

## 🧩 Dependencies

- **pyenchant** (voor Nederlandse woordcontrole)  
Zorg dat de NL woordenlijst geïnstalleerd is.

---

## ❤️ Credits

Gemaakt voor een 18+ Nederlandse Discord community, met liefde.  
WoordspelV3 is een doorontwikkeling van WoordspelV2 met meer functies, stabiliteit en flexibiliteit.

