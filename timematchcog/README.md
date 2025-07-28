# TimeMatchCog

A Red DiscordBot cog that sends a notification in a chosen text channel whenever the hour and minute match (e.g., 13:13, 22:22).

The reason is a kids-games they play in the Netherlands.
When the hour and minute match, they have to touch the ground

## Features

- Sends a message like `HET IS 13:13 ... TIK DE GROND!` when hour and minute match.
- Admins can set the notification channel with a command.

## Setup

1. Place the `timematchcog` folder in your Red cogs directory.
2. Load the cog:
   ```
   [p]load timematchcog
   ```
3. Set the channel for notifications:
   ```
   [p]settimematchchannel #your-channel
   ```

## Requirements

- Redbot V3
- discord.py

## Commands

- `[p]settimematchchannel <channel>`: Set the channel for time match notifications (admin only).

## License

MIT