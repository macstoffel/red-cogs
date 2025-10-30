# BumpReminder (Red-DiscordBot Cog)

Automatische bump reminders voor Disboard.

✅ Detecteert wanneer een Disboard bump is gelukt (“Bump done”)
✅ Wacht automatisch 2 uur
✅ Stuurt een reminder in een ingesteld kanaal
✅ Pingt een ingestelde rol

---

## ✅ Installatie (via Discord)

1) **Voeg de repo toe aan Redbot**
   Typ in een kanaal waar je bot toegang heeft (met jouw adminrechten):

   ```
   [p]repo add MacStoffel https://github.com/MacStoffel/redcogs
   ```

2) **Installeer de cog**
   ```
   [p]cog install MacStoffel bumpreminder
   ```

3) **Laad de cog**
   ```
   [p]load bumpreminder
   ```

---

## ✅ Configuratie

Stel in welk kanaal en welke rol gepingd moet worden:

```
[p]bumpset #bump @Bumpers
```

- `#bump` = kanaal waar de herinneringen komen
- `@Bumpers` = rol die gepingd wordt zodra het weer tijd is om te bumpen

Vanaf nu:
- Zodra Disboard meldt dat een bump is gelukt, telt de cog 2 uur af
- Na 2 uur verschijnt automatisch een reminder in het ingestelde kanaal

---
Alle settings:

- [p]bumpset #kanaal @rol
  - Doel: Stel reminder-kanaal en reminder-rol in.
  - Perms: manage_guild / admin
  - Voorbeeld: [p]bumpset #bumpkanal @Bumpers

- [p]bumpsettings
  - Doel: Toon huidige bump- en thank-you instellingen (kanaal, rol, thank-message, status).
  - Perms: manage_guild / admin

- [p]bumpthanks_setchannel [#kanaal]
  - Doel: Stel kanaal in waar het "thank you" bericht na een bump wordt gestuurd. Geen argument = reset naar bump-kanaal.
  - Perms: manage_guild / admin
  - Voorbeeld: [p]bumpthanks_setchannel #dankkanaal

- [p]bumpthanks_setmessage <bericht>
  - Doel: Stel de thank-you boodschap in. Gebruik {user} om de beller te mentionen.
  - Perms: manage_guild / admin
  - Voorbeeld: [p]bumpthanks_setmessage Thanks for bumping, {user}!

- [p]bumpthanks_toggle
  - Doel: Schakel het thank-you bericht aan/uit.
  - Perms: manage_guild / admin

---

## ✅ Vereisten
- De bot moet in het ingestelde kanaal:
  - berichten kunnen lezen
  - berichten kunnen versturen
  - de gekozen rol kunnen vermelden (mention)

---

## ✅ Verwijderen of uitschakelen

Cog unloaden:
```
[p]unload bumpreminder
```

Cog verwijderen:
```
[p]cog uninstall bumpreminder bumpreminder
```

Repo verwijderen:
```
[p]repo remove bumpreminder
```

---

## ✅ Auteurs
- MacStoffel

## ✅ License
MIT
