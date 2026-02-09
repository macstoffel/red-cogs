
# Confession Cog (Red v3)

Een configureerbare anonieme biecht-cog voor Red-DiscordBot v3.

## Features
- Anoniem biecht-kanaal
- Logging met gebruiker + ID
- Paarse embeds
- Bijlagen anoniem
- Cooldown per gebruiker
- Profanity / blacklist filter
- Nummering van biechten

## Installatie

[p]repo add MacStoffel https://github.com/MacStoffel/red-cogs

[p]cog install MacStoffel confession

[p]load confession

## Configuratie

- [p]confession setconfession #biecht
- [p]confession setlog #biecht-logs
- [p]confession setcooldown 300
- [p]confession addbadword
- [p]confession removebadword
- [p]confession settings
- [p]confession setcounter 42
-> Biecht-teller staat nu op 42

- [p]confession resetcounter
-> Teller staat weer op 0

## Permissies
Read Messages, Send Messages, Manage Messages
