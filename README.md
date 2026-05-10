# ha-homebox-addon

[Homebox](https://github.com/sysadminsmedia/homebox) as a Home Assistant Supervisor Add-on, with a built-in conversation agent so you can ask HA *"where is my X?"*.

<!-- Badges -->
[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FAmantux%2Fha-homebox-addon)

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=homebox)

[![CI](https://github.com/Amantux/ha-homebox-addon/actions/workflows/ci.yml/badge.svg)](https://github.com/Amantux/ha-homebox-addon/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA Supervisor Add-on](https://img.shields.io/badge/Home%20Assistant-Add--on-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/addons/)
[![HA Integration](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/integrations/)
[![Architectures](https://img.shields.io/badge/arch-amd64%20%7C%20aarch64%20%7C%20armv7-blue)](homebox/config.json)

---

## Installation

### 1 — Add-on (runs the Homebox server locally)

Click the button to add this repository to your HA instance, then install **Homebox**:

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FAmantux%2Fha-homebox-addon)

Or manually:
1. In HA go to **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
2. Add `https://github.com/Amantux/ha-homebox-addon`.
3. Install **Homebox**, configure timezone, and click **Start**.
4. Access the UI via the **Homebox** sidebar panel (ingress) or port `7745`.

### 2 — Conversation Integration (natural-language queries)

Click the button to start the integration setup:

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=homebox)

Or manually:
1. Copy `custom_components/homebox/` into your HA `config/custom_components/` folder.
2. Restart Home Assistant.
3. Go to **Settings → Integrations → Add → Homebox**.
4. Enter the Homebox URL (`http://localhost:7745`) and an API token from **Profile → API Tokens**.
5. Go to **Settings → Voice Assistants** and select **Homebox** as the conversation agent.

You can then ask things like:
- *"Where is my hammer?"*
- *"What's in the garage?"*
- *"Find the camping tent"*
- *"Search for power tools"*
- *"Show me everything in the basement"*

## Lovelace Search Card

See [`homebox/DOCS.md`](homebox/DOCS.md#lovelace-card-example) for a ready-to-paste dashboard card that lets you type a question and see the answer inline.

## Repository Structure

```
repository.json                    ← HA add-on hub manifest
homebox/                           ← Add-on (Supervisor / Docker)
  config.json, Dockerfile, run.sh
custom_components/homebox/         ← HA custom integration (conversation agent)
tests/                             ← pytest suite (no HA install required)
```
