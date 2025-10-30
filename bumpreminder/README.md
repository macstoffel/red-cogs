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

## Beschikbare commands

- `[p]bumpset #kanaal @rol` — Stel reminder-kanaal en reminder-rol in. (manage_guild/admin)  
- `[p]bumpsettings` — Toon huidige bump- en thank-you instellingen. (manage_guild/admin)  
- `[p]bumpthanks_setchannel [#kanaal]` — Kies kanaal voor thank-you (geen arg = gebruik bump-kanaal). (manage_guild/admin)  
- `[p]bumpthanks_setmessage <bericht>` — Stel thank-you boodschap in; gebruik `{user}` voor mention. (manage_guild/admin)  
- `[p]bumpthanks_toggle` — Schakel thank-you bericht aan/uit. (manage_guild/admin)

---

## 🧪 Testen & Debug (toegevoegd)

Gebruik deze commando's om te controleren of de cog werkt en waarom er geen reminder gestuurd wordt:

- `[p]bumpdebug`  
  - Toont de huidige instellingen en last_bump timestamp (human readable).

- `[p]bumptest <delay_seconds>`  
  - Simuleert een bump: stuurt direct een thank-you en plant een reminder na <delay_seconds> (standaard 10s). Handig om snel reminders te testen.

- Logger output  
  - De cog schrijft debug/info logs naar de Red-console (logger `red.bumpreminder`).  
  - Tail de Red log in je server/console om fouten en waarschuwingen te zien.

## ⚠️ Troubleshooting: geen reminder?

Controleer het volgende als je geen reminder ontvangt:

1. Permissions
   - Bot moet berichten kunnen lezen en verzenden in het target kanaal en de rol mogen mentionen.

2. Config
   - Controleer met `[p]bumpsettings` dat `channel_id` en `role_id` ingesteld zijn.

3. Testen
   - Run `[p]bumptest 10` en bekijk of:
     - direct de thank-you verschijnt,
     - na ~10s de reminder verschijnt,
     - er fouten in de Red-console staan.

4. Bump-detectie
   - De cog detecteert bumps via bekende bump-bot IDs en inhoud van embeds/berichten. Als jouw bump-bot een andere ID gebruikt, voeg die toe in de cog (variabele `BUMP_BOT_IDS`).

5. Logs
   - Bekijk de Red-console voor logger lines zoals:
     - "Processing bump event ..."  
     - "Sent bump reminder ..."  
     - of permission-warnings/exceptions.

## ✅ Tips

- Gebruik `[p]bumptest` eerst voordat je op echte bumps vertrouwt.  
- Voeg extra bump-bot IDs toe indien jouw bump-tool een andere author ID gebruikt.

---

## ✅ Auteurs
- MacStoffel

## ✅ License
MIT
