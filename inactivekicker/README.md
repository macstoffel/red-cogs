# InactiveKicker

Een **Redbot cog** waarmee je inactieve leden kunt tonen of automatisch kicken.

## 🔗 Installatie via GitHub

Voeg eerst je GitHub repo toe aan je Redbot instance:

[p]repo add MacStoffel https://github.com/MacStoffel/red-cogs
[p]cog install MacStoffel inactivekicker
[p]load inactivekicker

## ⚙️ Gebruik
[p]inactive <rol> <dagen> [show|kick]

- **rol** – De rol waarin je wilt zoeken (bijv. `@Members`)  
- **dagen** – Het aantal dagen inactief  
- **actie** – `show` (standaard) of `kick`  

### Voorbeelden

- `!inactive @Members 365 show`  
  ➝ Laat alle leden zien die langer dan 365 dagen inactief zijn.  

- `!inactive @Members 365 kick`  
  ➝ Kickt deze leden uit de server.  

## 🔍 Hoe werkt het?

- De cog slaat de **laatste activiteit** op van leden (berichten en voice-join).  
- Als er geen activiteit bekend is, wordt `joined_at` gebruikt als fallback.  
- Zo kun je betrouwbaarder inactiviteit meten.  

## ⚠️ Waarschuwing

Gebruik altijd eerst **show** om te controleren wie er gekickt zal worden.  
De bot moet de permissie **Kick Members** hebben om leden te verwijderen.

---

## 📜 Info

- **Auteur**: MacStoffel  
- **Tags**: moderation, inactive, kick  
