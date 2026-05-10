# Copilot Instructions

## What This Is

A Home Assistant Supervisor Add-on that packages the [Homebox](https://github.com/sysadminsmedia/homebox) inventory management system. The add-on pulls the pre-built Homebox Go binary from the official Docker image and wraps it in a Home Assistant-compatible container.

There are no build, test, or lint commands — this repo contains only configuration and a Dockerfile.

## Architecture

```
repository.json                   — HA add-on hub manifest (repo root)
homebox/                          — The Supervisor add-on (Docker container)
  config.json                       HA add-on manifest: startup, ports, ingress, options/schema
  Dockerfile                        Copies Homebox binary from ghcr.io/sysadminsmedia/homebox:latest
  build.json                        Maps arch → HA base image (injected as ARG BUILD_FROM)
  run.sh                            Reads bashio options, sets HBOX_* env vars, execs /homebox
  DOCS.md                           User-facing documentation shown in HA UI
custom_components/homebox/        — HA custom integration (conversation agent)
  api.py                            Async REST client: GET /api/v1/items?search=...
  conversation.py                   ConversationEntity wired to the Homebox API
  config_flow.py                    UI flow: configure Homebox URL + API token
  translations/en.json              Config flow UI strings
tests/                            — pytest suite (stubs HA modules, no HA install needed)
```

The add-on and the custom component are independent:
- **Add-on** → runs the Homebox Go binary in a Supervisor container, persists data to `/data/homebox`
- **Custom component** → connects to the running Homebox via its REST API, registers as a HA conversation agent


## Key Conventions

### HA add-on structure (Supervisor requirements)
- `homebox/config.json` must have `startup`, `boot`, `options` + `schema` (not nested option objects), and valid JSON throughout
- `ports` keys are `"<container_port>/tcp"` → host port integer (e.g. `"7745/tcp": 7745`)
- `ingress: true` + `ingress_port` wires the add-on into the HA sidebar without exposing a port externally
- `map: ["data:rw"]` grants the add-on read/write to `/data` (persisted by Supervisor)
- `run.sh` shebang must be `#!/usr/bin/with-contenv bashio` to get the HA environment + `bashio::config` helper
- Homebox data directory: `/data/homebox` (set via `HBOX_STORAGE_DATA`)
- Homebox listens on port `7745` (set via `HBOX_WEB_PORT=7745`)

### Dockerfile pattern
```dockerfile
ARG BUILD_FROM
FROM ${BUILD_FROM}          # HA Supervisor injects arch-specific base image from build.json
COPY --from=ghcr.io/sysadminsmedia/homebox:latest /app/homebox /homebox
```

### Updating Homebox version
Change the image tag in `homebox/Dockerfile`:
```dockerfile
COPY --from=ghcr.io/sysadminsmedia/homebox:<tag> /app/homebox /homebox
```

### Adding add-on configuration options
1. Add default value to `options` in `homebox/config.json`
2. Add type/validation to `schema` in `homebox/config.json`
3. Read it in `homebox/run.sh` with `bashio::config 'option_name'`

