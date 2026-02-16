# AttachmentsControl

Een volledig configureerbare attachment anti-spam cog voor Red-DiscordBot.

Deze cog voorkomt attachment spam door:

- Een limiet in te stellen op het aantal attachments binnen een tijdvenster
- Automatisch een timeout toe te passen bij overschrijding
- Een escalatie-timeout toe te passen bij herhaling binnen een bepaalde periode
- Logs te sturen naar een instelbaar logkanaal
- DM-waarschuwingen te sturen naar overtreders
- Per-server configuratie op te slaan via Red Config

---

# Features

- Configureerbare rol (bijv. `nieuw-lid`)
- Instelbaar maximum aantal attachments
- Instelbaar tijdvenster (seconden)
- Instelbare eerste timeout (minuten)
- Instelbare escalatie timeout (uren)
- Instelbare escalatieperiode (minuten)
- Instelbaar logkanaal
- Per-guild configuratie
- Geen berichten worden verwijderd
- Volledig command-based configuratie
- Persistent via Red Config

---

# Installatie via GitHub

1️⃣ Voeg de repository toe aan Red:
```
[p]repo add MacStoffel https://github.com/MacStoffel/AttachmentsControl
```

2️⃣ Installeer de cog:
```
[p]cog install MacStoffel AttachmentsControl
```

3️⃣ Laad de cog:
```
[p]load AttachmentsControl
```

---

# Handmatige installatie

1. Ga naar de RedBot cogs map:
```
redbot/cogs/
```
2. Maak een map:
```
AttachmentsControl/
```
3. Plaats hierin:
- attachmentscontrol.py
- __init__.py
- info.json

4. Start of reload de bot
5. Laad de cog:
```
[p]load AttachmentsControl
```

---

# Configuratie

Gebruik de commands:
```
[p]attachcontrol
```
Alle commands vereisen Administrator of Manage Server permissie.

## Enable / Disable
```
[p]attachcontrol enable
[p]attachcontrol disable
```

## Rol instellen
```
[p]attachcontrol role nieuw-lid
```

## Max attachments
```
[p]attachcontrol max 4
```

## Tijdvenster
```
[p]attachcontrol window 30
```

## Eerste timeout
```
[p]attachcontrol firsttimeout 30
```

## Escalatie timeout
```
[p]attachcontrol escalation 24
```

## Escalatieperiode
```
[p]attachcontrol escalationwindow 30
```

## Logkanaal
```
[p]attachcontrol logchannel #systeemlogs
```

---

# Voorbeeldconfiguratie
```
[p]attachcontrol enable
[p]attachcontrol role nieuw-lid
[p]attachcontrol max 4
[p]attachcontrol window 30
[p]attachcontrol firsttimeout 30
[p]attachcontrol escalation 24
[p]attachcontrol escalationwindow 30
[p]attachcontrol logchannel #systeemlogs
[p]attachcontrol show
```
Resultaat:
- 4 attachments toegestaan binnen 30 seconden
- 5e attachment → 30 minuten timeout
- Binnen 30 minuten opnieuw attachment → 24 uur timeout
- DM naar gebruiker
- Log in #systeemlogs
- Berichten blijven staan

---

# Vereisten
- Moderate Members permissie
- View + Send Messages in logkanaal
- Botrol boven gecontroleerde rol

---

# Hoe het werkt
- Cog houdt timestamps per gebruiker bij
- Oude timestamps buiten tijdvenster worden verwijderd
- Eerste overtreding → timeout + escalatie-flag
- Herhaling binnen escalatieperiode → escalatie timeout
- Escalatie-flag vervalt automatisch

---

# Data opslag
- Per guild: enabled status, rol ID, limieten, timeout instellingen, logkanaal
- Timestamps en flags in geheugen
- Geen permanente opslag van berichten of inhoud

---

# Troubleshooting
- Timeout werkt niet: controleer permissies, rolvolgorde, cog enabled, juiste rol
- Logs niet zichtbaar: controleer logkanaal en bot toegang

---

# Aanbevolen uitbreidingen
- Per-kanaal whitelist
- Automatische ban na X escalaties
- Strike-systeem
- Status command / dashboard output
- Persistent escalation tracking
- Memory optimalisatie voor grote servers

---

# Licentie
MIT License

