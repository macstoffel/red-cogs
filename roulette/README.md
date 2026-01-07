# 🎰 Roulette – Red-DiscordBot Cog

**Roulette** is een uitgebreide takenroulette voor **Red-DiscordBot (v3.5+)**.  
Gebruikers kunnen via knoppen een **random taak** aanvragen (mannen/vrouwen), bewijs leveren en – afhankelijk van de instellingen – goedkeuring krijgen van moderators.

De cog is volledig configureerbaar en bevat **logging, cooldowns, statistieken**, een optioneel **approve-systeem**, en **tasks persistent via JSON-bestand**.

---

## ✨ Functionaliteiten

- 🎯 Twee knoppen: **Mannen-taak** & **Vrouwen-taak**
- 📋 Random taken per categorie
- 📸 Bewijs leveren in een apart kanaal
- ✅ Optioneel **approve-systeem** (aan/uit)
- 🛡️ Rol-gebaseerde goedkeuring
- 🧾 Uitgebreide logging in logkanaal
- ⏱️ Instelbare cooldown (bij geen bewijs)
- 📊 Statistieken per gebruiker
- 💜 Paarse embeds
- 🔒 Persistent via **tasks.json**

---

## 📁 Repo-structuur

```
roulette/
├── info.json
├── __init__.py
├── roulette.py
└── tasks.json  # Mannen/vrouwen-taken
```

- `tasks.json` bevat taken en blijft persistent bij herstart van de bot.

### JSON voorbeeld (tasks.json)

```json
{
  "male": [
    "Doe 20 push-ups",
    "Doe 10 squats"
  ],
  "female": [
    "Maak een selfie",
    "Zing een liedje"
  ]
}
```

---

## 🚀 Installatie

### 1️⃣ Voeg de repo toe
```bash
[p]repo add roulette_repo <GITHUB_REPO_URL>
```

### 2️⃣ Installeer de cog
```bash
[p]cog install roulette_repo roulette
```

### 3️⃣ Laad de cog
```bash
[p]load roulette
```

---

## ⚙️ Basis setup

```text
[p]roulette setup #knoppenkanaal #bewijskanaal
```

---

## 📝 Logkanaal instellen

```text
[p]roulette logchannel #logkanaal
```

---

## ✅ Approve-systeem

### Approve verplicht aan/uit
```text
[p]roulette approve on
[p]roulette approve off
```

### Rol die mag goedkeuren
```text
[p]roulette approverole @Moderator
```

---

## 🎯 Taken beheren

### Taak toevoegen/verwijderen (JSON persist)
```text
[p]roulette addtask male <taak>
[p]roulette addtask female <taak>
[p]roulette removetask male 0
[p]roulette removetask female 1
[p]roulette tasks  # Lijst alle taken
```

---

## ⏱️ Cooldown instellen

```text
[p]roulette cooldown <uren>
```

---

## 📊 Statistieken

```text
[p]roulette stats
```

---

## ⚙️ Instellingen bekijken

```text
[p]roulette settings
```

---

## ❤️ Credits

Gemaakt voor Red-DiscordBot  
Veel plezier met Roulette! 🎰💜

Gr MacStoffel