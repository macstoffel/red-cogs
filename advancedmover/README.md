# AdvancedMover (Production Edition)

Production-ready message moving & copying cog for Red-DiscordBot.

---

## Features

### Core
- Move messages between channels and threads
- Copy messages between channels and threads
- Optimized: 1 webhook per destination
- Rate-limit friendly processing
- Progress tracking every 10 messages
- Confirmation prompt for large actions (>100 messages)

### Advanced Filters (combine freely)
- Filter by user
- Filter by time (last X minutes)
- Filter by start ID
- Filter by end ID

### Thread Support
- Move to existing threads
- Create a new thread and move messages into it

---

## Installation

```
[p]repo add MacStoffel https://github.com/MacStoffel/redcogs.git
[p]cog install MacStoffel advancedmover
[p]load advancedmover
```

---

## Commands

bericht verplaatsen:

[p]moveid <destination> <berichtID>


### Advanced Move
[p]advmove <destination> [member] [minutes] [start_id] [end_id]

Example:
[p]advmove #thread @User 30

Moves messages from @User from the last 30 minutes.

---

### Advanced Copy
[p]advcopy <destination> [member] [minutes] [start_id] [end_id]

---

### Create New Thread & Move
[p]advmovetonewthread "Thread Name"

---

## Required Permissions

Bot requires:

- Manage Messages
- Manage Webhooks
- Send Messages
- Read Message History
- Create Public Threads (for thread creation)

---

## Notes

- Discord does not support native message moving.
- Messages are reposted via webhook and optionally deleted.
- Large operations may take time.
- Confirmation required for operations over 100 messages.

---

## Compatibility

- Red-DiscordBot 3.5+
- Supports text channels and threads