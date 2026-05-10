# Copilot Instructions

## What This Is

A Home Assistant Supervisor Add-on that packages the [Homebox](https://github.com/sysadminsmedia/homebox) inventory management system. The add-on pulls the pre-built Homebox Go binary from the official Docker image and wraps it in a Home Assistant-compatible container.

There are no build, test, or lint commands — this repo contains only configuration and a Dockerfile.

## Architecture

```
Dockerfile        — Multi-stage: copies /homebox binary from homebox/homebox:latest into HA base image
config.json       — HA add-on manifest (name, slug, ports, supported arches, user-configurable options)
build.json        — Maps each arch (amd64, armv7, aarch64) to the corresponding HA base image
repository.json   — Identifies this repo as an HA add-on hub/repository
custom_components/homebox/  — Placeholder directory (currently empty)
```

The Dockerfile uses `ARG BUILD_FROM` / `FROM ${BUILD_FROM}` — this is the required HA Supervisor pattern. The build system injects the correct arch-specific base image from `build.json` at build time.

## Key Conventions

### config.json schema
This file must conform to the [HA Add-on configuration schema](https://developers.home-assistant.io/docs/add-ons/configuration). Key fields:
- `slug` must be lowercase and match the directory name under `custom_components/`
- `arch` lists supported architectures; must align with the keys in `build.json`
- `ports` maps `"host:container/protocol"` strings
- `options` defines user-configurable settings exposed in the HA UI

### Updating the Homebox version
Change the image tag in the Dockerfile's `COPY --from=` line:
```dockerfile
COPY --from=homebox/homebox:<tag> /homebox /homebox
```

### Adding add-on configuration options
1. Add the option to `config.json` under `options` with `type`, `description`, and optionally `default`
2. Pass the value to the binary via `ENTRYPOINT` or an `run.sh` script if environment variable injection is needed
