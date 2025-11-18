# VoicePing Cog for Redbot

This is a Red DiscordBot cog that sends a message to a designated text channel when a user joins a voice channel — with support for excluding specific voice channels.

## Features

- 🔔 Pings when users join voice channels
- 🚫 Exclude specific voice channels
- 🛠 Admin-only setup commands

## Commands

### Setup

```bash
[p]voiceping settextchannel #text-channel
[p]voiceping addexclude VoiceChannel
[p]voiceping removeexclude VoiceChannel
[p]voiceping listexcluded
```

## Installation

```bash
[p]repo add MacStoffel https://github.com/MacStoffel/red-cogs
[p]cog install MacStoffel voiceping
[p]load voiceping
```

## License

MIT
