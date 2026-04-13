# WoordspelV3 — Redbot Cog

WoordspelV3 is de vernieuwde, verbeterde en uitgebreidere versie van het Nederlandse woordketting‑spel voor Redbot.  
Deze versie bevat persistente scores, admin‑beheer, een optionele score‑behoud‑modus, en een verbeterd taak‑ en pauzesysteem.

Alle commands beginnen met **$ws**.

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
  - `$ws taakadd "<taak>"`
  - `$ws taakremove <id>`
  - `$ws taken`

### ✔ Time-out systeem
- Standaard 5 minuten
- Aanpasbaar via:
  - `$ws timeout <seconden>`

### ✔ Configureerbaar takenkanaal
- Stel zelf het kanaal in met:
  - `$ws taskchannel #kanaalnaam`

### ✔ Persistente score-opslag (NIEUW in V3)
- Score blijft bewaard bij een Redbot‑herstart
- Highscore blijft bewaard
- Laatste woord en doelpunten worden opgeslagen

### ✔ Admin scorebeheer (NIEUW in V3)
Beheerders kunnen nu:
- De score aanpassen:  
  `$ws setscore <waarde>`
- De highscore aanpassen:  
  `$ws sethighscore <waarde>`

### ✔ Optie: score behouden bij taak-succes (NIEUW in V3)
- Normaal wordt de score gereset bij een fout woord
- In V3 kun je instellen dat de score behouden blijft als de taak op tijd wordt uitgevoerd
- Aan/uit via:  
  `$ws keepscore true/false`

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
| `$ws start [doelpunten]` | Start een nieuwe sessie |
| `$ws stop` | Stopt het spel |
| `$ws totaal` | Huidige score |
| `$ws highscore` | Hoogste score |
| `$ws help` | Overzicht embeds |

### Taakbeheer
| Command | Functie |
|--------|---------|
| `$ws taakadd "<tekst>"` | Voegt een taak toe |
| `$ws taakremove <id>` | Verwijdert een taak |
| `$ws taken` | Bekijk alle taken |

### Configuratie
| Command | Functie |
|--------|---------|
| `$ws taskchannel #kanaal` | Stel takenkanaal in |
| `$ws timeout <seconden>` | Zet taak time-out |
| `$ws keepscore true/false` | Score behouden bij taak-succes |

### Admin scorebeheer (nieuw)
| Command | Functie |
|--------|---------|
| `$ws setscore <waarde>` | Pas de huidige score aan |
| `$ws sethighscore <waarde>` | Pas de highscore aan |

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

