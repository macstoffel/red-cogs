# 🔥 AlphabetKink – Red DiscordBot Cog

![discord](https://img.shields.io/badge/Discord-7289DA?logo=discord&logoColor=white)
![python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![redbot](https://img.shields.io/badge/Red--DiscordBot-cog-purple)
![status](https://img.shields.io/badge/Status-Stable-success)

Een **kinky alfabet spel** voor Red-DiscordBot.
Spelers typen BDSM / fetish / kinky woorden die beginnen met de juiste letter.
Begint bij **A**, eindigt bij **Z**. Fout woord? → Reset.
Z gehaald? → Feest & nieuw spel.

✅ Scores per speler
✅ Top 10 scorebord
✅ Standaard woordenlijst + JSON import/export
✅ Embed-style reacties
✅ Kanaal instelbaar
✅ Speler mag niet 2x achter elkaar

## ✅ Installatie

```
[p]repo add alphabetkink https://github.com/<jouw-gebruikersnaam>/<repo>.git
[p]cog install alphabetkink alphabetkink
[p]load alphabetkink
```

## ✅ Commands

| Command | Uitleg |
|---------|--------|
| **[p]kinkalfabet** | Start/reset spel |
| **[p]kinksetchannel #kanaal** | Speelkanaal instellen |
| **[p]kinkscore** | Bekijk je score |
| **[p]kinktop** | Top 10 spelers |
| **[p]kinkexport** | Exporteer woordenlijst |
| **[p]kinkimport** | Importeer woordenlijst |

## ✅ Woordenlijst

- Bij eerste run wordt automatisch `kink_words.json` aangemaakt
- `$kinkexport` → download woordenlijst
- Upload `kink_words.json` + `$kinkimport` → nieuwe lijst

## ✅ Voorbeeld

```json
{
  "A": ["aftercare", "anal"],
  "B": ["bondage", "ballgag", "buttplug"],
  "C": ["chastity", "collar", "consent"],
  "D": ["dom", "discipline", "dominant"],
  "E": ["edgeplay", "electroplay"],
  "F": ["fetish", "fixatie", "flogger"],
  "G": ["gag", "gimp"],
  "H": ["harnas", "handcuffs"],
  "I": ["impactplay"],
  "J": ["jute"],
  "K": ["kinky", "kettingen"],
  "L": ["latex", "leather"],
  "M": ["masochist", "master", "mascara-running"],
  "N": ["needleplay", "nippleclamps"],
  "O": ["opper", "o-ring"],
  "P": ["paddle", "petplay"],
  "Q": ["queening"],
  "R": ["ropes", "rigger"],
  "S": ["sub", "sadist", "spreaderbar"],
  "T": ["teasing", "tapeplay"],
  "U": ["uniformplay"],
  "V": ["vettex", "vibrator"],
  "W": ["whip", "waxplay"],
  "X": ["x-frame"],
  "Y": ["yoke"],
  "Z": ["zipper", "zelfbinding"]
}
```

Veel plezier!
