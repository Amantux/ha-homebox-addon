# ha-homebox-addon

[Homebox](https://github.com/sysadminsmedia/homebox) as a Home Assistant Supervisor Add-on, with a built-in conversation agent so you can ask HA *"where is my X?"*.

## Installation

### Add-on (runs the Homebox server)

1. In HA, go to **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
2. Add `https://github.com/Amantux/ha-homebox-addon`.
3. Install **Homebox**, configure timezone, and click **Start**.
4. Access the UI via the **Homebox** sidebar panel (ingress) or port `7745`.

### Conversation Integration (natural-language queries)

1. Copy `custom_components/homebox/` into your HA `config/custom_components/` folder.
2. Restart Home Assistant.
3. Go to **Settings → Integrations → Add → Homebox**.
4. Enter the Homebox URL (`http://localhost:7745`) and an API token from **Profile → API Tokens**.
5. Go to **Settings → Voice Assistants** and select **Homebox** as the conversation agent.

You can then ask things like *"Where is my hammer?"* or *"Find the camping tent"*.

## Repository Structure

```
repository.json                    ← HA add-on hub manifest
homebox/                           ← Add-on (Supervisor / Docker)
  config.json, Dockerfile, run.sh
custom_components/homebox/         ← HA custom integration (conversation agent)
tests/                             ← pytest suite (no HA install required)
```
