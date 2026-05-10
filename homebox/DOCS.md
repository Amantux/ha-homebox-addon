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
- *"What's in the garage?"*
- *"Show me everything in the basement"*
- *"Search for power tools"*
- *"Do you know where my screwdriver is?"*

## Lovelace Card Example

The following configuration adds an inventory search card to your dashboard.

### Step 1 — Add helpers

Go to **Settings → Devices & Services → Helpers** and create two text helpers:

| Name | Entity ID |
|------|-----------|
| Homebox Query | `input_text.homebox_query` |
| Homebox Result | `input_text.homebox_result` |

### Step 2 — Add a script

Add this to `scripts.yaml` (or create via the Scripts UI):

```yaml
homebox_search:
  alias: "Homebox Search"
  sequence:
    - service: conversation.process
      data:
        text: "{{ states('input_text.homebox_query') }}"
        agent_id: conversation.homebox  # adjust to your agent entity id
      response_variable: agent_reply
    - service: input_text.set_value
      target:
        entity_id: input_text.homebox_result
      data:
        value: "{{ agent_reply.response.speech.plain.speech }}"
```

### Step 3 — Add the Lovelace card

Paste this into your dashboard YAML (Raw Configuration Editor):

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Inventory Search
    entities:
      - entity: input_text.homebox_query
        name: Search term or question

  - type: button
    name: Search Homebox
    tap_action:
      action: call-service
      service: script.homebox_search

  - type: markdown
    title: Results
    content: >
      {{ states('input_text.homebox_result') or '_Ask something above…_' }}
```

**Example queries to try in the card:**
- `where is my hammer?`
- `what's in the garage?`
- `find camping gear`
- `search for power drill`

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
