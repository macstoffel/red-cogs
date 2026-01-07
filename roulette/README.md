# 🎰 Roulette – Red-DiscordBot Cog

**Roulette** is een uitgebreide takenroulette voor **Red-DiscordBot (v3.5+)**.  
Gebruikers kunnen via knoppen een **random taak** aanvragen (mannen/vrouwen), bewijs leveren en – afhankelijk van de instellingen – goedkeuring krijgen van moderators.

De cog is volledig configureerbaar en bevat logging, cooldowns, statistieken en een optioneel approve-systeem.

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
- 🔒 Persistent via Red Config

---

## 📁 Repo-structuur

```
roulette/
├── info.json
├── __init__.py
└── roulette.py
```

---

## 🚀 Installatie

### 1️⃣ Voeg de repo toe
```bash
[p]repo add MacStoffel https://github.com/MacStoffel/red-cogs
```

### 2️⃣ Installeer de cog
```bash
[p]cog install MacStoffel roulette
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

---

### Rol die mag goedkeuren
```text
[p]roulette approverole @Moderator
```

---

## 🎯 Taken beheren

```text
[p]roulette addtask male <taak>
[p]roulette addtask female <taak>
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
