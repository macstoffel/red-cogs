# ForbiddenWords

Een Red-DiscordBot Cog voor het beheren van verboden woorden.

## Functies

- Verboden woorden toevoegen
- Verboden woorden verwijderen
- Woordenlijst bekijken
- Strafpunten per gebruiker
- Top 10 ranglijst
- Punten handmatig beheren
- Automatische timeout bij ieder 10e punt
- Werkt per server afzonderlijk
- Paarse embeds voor alle meldingen

## Installeren

Repository toevoegen:

```text
[p]repo add repo add MacStoffel https://github.com/MacStoffel/redcogs
```

Cog installeren:

```text
[p]cog install MacStoffel forbiddenwords
```

Cog laden:

```text
[p]load forbiddenwords
```

## Commando's

### Woord toevoegen

```text
[p]forbidden add woord
```

### Woord verwijderen

```text
[p]forbidden remove woord
```

### Woordenlijst bekijken

```text
[p]forbidden list
```

### Eigen score

```text
[p]forbidden score
```

### Score van gebruiker

```text
[p]forbidden score @Gebruiker
```

### Top 10

```text
[p]forbidden top10
```

### Punten instellen

```text
[p]forbidden points set @Gebruiker 5
```

### Punten toevoegen

```text
[p]forbidden points add @Gebruiker 5
```

### Punten verwijderen

```text
[p]forbidden points remove @Gebruiker 5
```

### Punten resetten

```text
[p]forbidden points reset @Gebruiker
```

## Permissions

Voor automatische timeouts heeft de bot nodig:

- Moderate Members
- Manage Messages (optioneel)
- Send Messages
- Embed Links

## Guild specifiek

Alle instellingen zijn server-specifiek:

- Eigen verboden woorden per server
- Eigen strafpunten per server
- Eigen top 10 per server

Meerdere servers kunnen deze cog dus onafhankelijk van elkaar gebruiken.
