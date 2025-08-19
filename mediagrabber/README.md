# MediaGrabber

A Red DiscordBot cog that automatically saves uploaded media (attachments) from Discord channels to a local folder.

## Features

- Save all media from all channels, or only selected channels.
- Customizable save path.
- Easy setup and management via bot commands.

## Setup

1. Place the `mediagrabber` folder in your Red cogs directory.
2. Load the cog:
   ```
   [p]load mediagrabber
   ```
3. Configure the cog:
   - Set the save folder:
     ```
     [p]mediagrabber setpath /your/desired/folder
     ```
   - Enable saving from all channels:
     ```
     [p]mediagrabber enableall true
     ```
   - Or add specific channels:
     ```
     [p]mediagrabber addchannel #your-channel
     ```

## Commands

- `[p]mediagrabber setpath <path>` — Set the folder for saving media.
- `[p]mediagrabber enableall <true|false>` — Enable/disable saving from all channels.
- `[p]mediagrabber addchannel <channel>` — Add a channel to the save list.
- `[p]mediagrabber removechannel <channel>` — Remove a channel from the save list.
- `[p]mediagrabber status` — Show current settings.

## Requirements

- Redbot V3
- discord.py
- aiohttp

## License MIT