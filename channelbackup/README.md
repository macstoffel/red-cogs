
# ChannelBackup Cog

## Description
This Discord cog automatically backs up messages from selected text channels into local Markdown files. 
It appends new messages as they appear, so the log files are always up-to-date.

## Features
- Admin commands to add/remove channels and set backup folder
- Custom filename prefix per channel
- Messages appended to file in real-time
- Markdown format with author name and timestamp
- Config stored in `backup_config.json`

## Installation
1. Copy the `discord_backup_cog` folder into your bot's `cogs` directory.
2. Load the cog in your bot:
```python
await bot.load_extension("discord_backup_cog")
```
3. Make sure your bot has `Read Message History` and `View Channel` permissions.

## Commands
- `!add_channel #channel [custom_name]` – add channel to backup
- `!remove_channel #channel` – remove channel from backup
- `!set_backup_folder path` – set local folder for backups
- `!backup_now` – trigger manual backup

## Dependencies
- discord.py or compatible fork
- Python 3.8+
