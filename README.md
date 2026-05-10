# ha-homebox-addon

[Homebox](https://github.com/sysadminsmedia/homebox) as a Home Assistant Supervisor Add-on, with a built-in conversation agent so you can ask HA *"where is my X?"*. Runs 100% locally — no cloud required.

<!-- Badges -->
[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FAmantux%2Fha-homebox-addon)

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=homebox)

[![CI](https://github.com/Amantux/ha-homebox-addon/actions/workflows/ci.yml/badge.svg)](https://github.com/Amantux/ha-homebox-addon/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA Supervisor Add-on](https://img.shields.io/badge/Home%20Assistant-Add--on-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/addons/)
[![HA Integration](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/integrations/)
[![Architectures](https://img.shields.io/badge/arch-amd64%20%7C%20aarch64%20%7C%20armv7-blue)](homebox/config.json)

---

## How it works

The add-on builds Homebox from source with the Nuxt frontend compiled for the HA ingress path (`/homebox/`). At runtime an nginx sidecar rewrites all paths to the real ingress URL — this is the same pattern used by the official Mealie add-on and is the architecturally correct way to serve a single-page app through HA ingress.

```
Browser ─► HA Ingress ─► nginx (8099) ─► Homebox Go server (127.0.0.1:7745)
                           └─ sub_filter: /homebox/ → /api/hassio_ingress/TOKEN/
```

> **First install note**: the add-on builds from source (Node.js frontend + Go backend). Expect **~10 minutes** on first install. Subsequent starts use Docker layer cache and are fast.

---

## Installation

### 1 — Add-on (runs the Homebox server locally)

Click to add this repository, then install **Homebox**:

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FAmantux%2Fha-homebox-addon)

Or manually:
1. **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
2. Add `https://github.com/Amantux/ha-homebox-addon`
3. Install **Homebox**, set your timezone, click **Start**
4. The **Homebox** panel appears in your sidebar — click it to open the UI

### 2 — Conversation Integration (ask HA about your inventory)

Click to set up the integration:

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=homebox)

Or manually:
1. Copy `custom_components/homebox/` into your HA `config/custom_components/` folder
2. Restart Home Assistant
3. **Settings → Integrations → Add → Homebox**
4. Enter:
   - **URL**: `http://localhost:7745` (internal Homebox port — use this even though the UI is on ingress)
   - **API Token**: create one in Homebox at **Profile → API Tokens**
5. **Settings → Voice Assistants** → set conversation agent to **Homebox**

Ask things like:
- *"Where is my hammer?"*
- *"What's in the garage?"*
- *"Find the camping tent"*
- *"Search for power tools"*
- *"Show me everything in the basement"*
- *"What's stored in the attic?"*

## Lovelace Search Card

See [`homebox/DOCS.md`](homebox/DOCS.md#lovelace-card-example) for a ready-to-paste dashboard card with a search input and inline results.

## Repository Structure

```
repository.json                     ← HA add-on store manifest
homebox/                            ← Supervisor add-on
  Dockerfile                        ← 4-stage build: clone → node → go → alpine
  config.json                       ← Add-on manifest (ingress, arch, options)
  nginx.conf.tpl                    ← nginx ingress proxy template
  run.sh                            ← Entrypoint: reads Supervisor API, starts nginx + Homebox
  CHANGELOG.md                      ← Add-on changelog (read by HA Supervisor UI)
  DOCS.md                           ← Add-on docs + Lovelace card example
custom_components/homebox/          ← HA custom integration (conversation agent)
tests/                              ← pytest suite — 50 tests, no HA install required
```
