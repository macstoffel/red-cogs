# Prutser Cog

Een Red DiscordBot cog waarmee je tijdelijk de rol **prutser** aan een gebruiker kunt toekennen. Na een ingestelde tijd wordt de rol automatisch weer verwijderd.

## Functies

- Tijdelijk toekennen van de rol `prutser` aan een gebruiker
- Automatische verwijdering van de rol na een ingestelde tijd
- Handmatig verwijderen van de rol
- Instellen van standaardduur en logkanaal
- Overzicht van huidige prutsers en resterende tijd

## Installatie

1. Voeg deze repository toe aan je Red DiscordBot:
    ```
    [p]repo add prutser <repo-url>
    [p]cog install prutser prutser
    [p]load prutser
    ```

2. Zorg dat de rol `prutser` bestaat op je server.

## Commando’s

- `[p]prutser @user` – wijs iemand tijdelijk de prutser-rol toe
- `[p]prutser clear @user` – verwijder prutser-rol direct
- `[p]prutser status` – laat zien wie nu prutser is
- `[p]prutser duration 10m` – pas de standaardtijd aan (bijv. 10m of 1h)
- `[p]prutser tijd @user` – laat resterende tijd zien voor een gebruiker
- `[p]prutserlog #kanaal` – stel het logkanaal in
- `[p]prutser_settings` – toon de huidige instellingen

## Auteur

Gemaakt door MacStoffel

---

*Deze cog is bedoeld voor gebruik met [Red DiscordBot](https://docs.discord.red/).*