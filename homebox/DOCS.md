# Homebox Add-on Documentation

## Overview

Homebox is a self-hosted inventory and organization system for your home. This add-on runs the Homebox server locally inside Home Assistant.

## Setup

1. Install this add-on from the add-on store.
2. Configure options (see below) and click **Start**.
3. Access the UI via the **Homebox** sidebar panel or on port `7745`.
4. In the Homebox UI, go to **Profile → API Tokens** and create a token.

## Home Assistant Conversation Integration

To enable natural-language inventory queries ("where is my passport?"):

1. Install the **Homebox** custom integration from `custom_components/homebox/`.
2. Go to **Settings → Integrations → Add Integration → Homebox**.
3. Enter:
   - **URL**: `http://localhost:7745` (or the ingress URL)
   - **API Token**: the token you created above
4. Go to **Settings → Voice Assistants** and set the conversation agent to **Homebox**.

You can then ask things like:
- *"Where is my hammer?"*
- *"Find the camping tent"*
- *"Locate my passport"*

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `timezone` | `UTC` | Timezone for the Homebox server (e.g. `America/New_York`) |
| `log_level` | `info` | Log verbosity: `debug`, `info`, `warning`, `error` |

## Data Persistence

All inventory data is stored in `/data/homebox` inside the add-on, which is persisted across restarts and updates by the HA Supervisor.

## Ports

| Port | Description |
|------|-------------|
| `7745` | Homebox web UI (also available via HA ingress) |
