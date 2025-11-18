# MediaGrabber Cog

A [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) cog that automatically saves uploaded media (images, videos, files) to a local folder.

## Features
- Save attachments from **all channels** or **specific channels** you choose.
- Option to **organize files into per-server and per-channel subfolders**.
- Fully configurable via commands.
- Automatically creates folders if they don't exist.

## Commands
- `[p]mediagrabber setpath <path>` → Set save location.
- `[p]mediagrabber enableall <true|false>` → Enable/disable all channels.
- `[p]mediagrabber addchannel #channel` → Add a channel to save list.
- `[p]mediagrabber removechannel #channel` → Remove a channel from save list.
- `[p]mediagrabber organize <true|false>` → Enable/disable server/channel subfolders.
- `[p]mediagrabber status` → Show current settings.

## Installation
Clone or add this repo to your Red bot, then:
```
[p]load mediagrabber
```

## Requirements
- No extra requirements (uses aiohttp, already in Red).
