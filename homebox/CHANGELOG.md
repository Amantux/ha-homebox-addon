## 1.2.0
- **Architecture overhaul: build Homebox from source (proper ingress support)**
  Homebox has no native sub-path/base-URL support. Previous versions used a
  fragile nginx sub_filter approach trying to pattern-match 12+ variations of
  `/_nuxt/` paths in minified JS — a known hack that broke on new path formats.

  The correct approach (modelled after how the Mealie HA add-on works):
  1. Build the Nuxt frontend from source with `NUXT_APP_BASE_URL=/homebox/`.
     Nuxt 3 bakes this prefix into every compiled asset path AND into the Vue
     Router base in the compiled JavaScript.
  2. A single nginx `sub_filter '/homebox/' 'INGRESS_ENTRY/'` rewrites both
     asset URLs and the router base to the real HA ingress path at runtime.

  Multi-stage Dockerfile: Alpine clone → Node 22 frontend build → Go backend
  build (embeds custom frontend) → minimal Alpine runtime with nginx.
  First install builds from source (~10 min); subsequent installs use Docker
  layer cache.

- Reduce nginx sub_filter rules from 12 to 4 (set-theme.js, /api/ calls ×3,
  and the single catch-all /homebox/ → INGRESS_ENTRY rule)
- Remove dependency on `ghcr.io/sysadminsmedia/homebox:latest` pre-built image


- Fix Firefox/browser blocking iframe embed: strip Homebox X-Frame-Options: DENY,
  replace with X-Frame-Options: SAMEORIGIN so HA ingress can embed the UI in its panel
- Also strip upstream Content-Security-Policy which may block framing

## 1.1.8
- Fix sidebar/ingress: add nginx sidecar proxy with sub_filter path rewriting
  Homebox Nuxt SPA bakes absolute asset paths (/_nuxt/...) into binary at build time.
  Browser resolves them against HA root, bypassing the ingress proxy. nginx rewrites
  /_nuxt/, /set-theme.js, /api/v1 to include the full ingress_entry prefix.
- ingress_port changed to 8099 (nginx); Homebox internal on 127.0.0.1:7745

## 1.1.7
- Fix sidebar ingress: removed ports/ports_description conflict with ingress: true
- Fix changelog not showing in HA: moved CHANGELOG.md into add-on subdirectory

## 1.1.6
- Fix sidebar not working: use INGRESS_PORT env var injected by Supervisor
- Add ingress_stream: true for WebSocket/streaming support through HA proxy

## 1.1.5
- Version bump (no functional changes from 1.1.2)

## 1.1.2
- Fix s6-overlay-suexec PID 1 crash in LXC/Docker-supervised HA installs
- Switch base image to ghcr.io/sysadminsmedia/homebox:latest; exec /app/api as PID 1
- Replace bashio with POSIX sh + curl/jq reading Supervisor REST API
- Add hassio_api + hassio_role for SUPERVISOR_TOKEN config injection

## 1.1.1
- Sync integration manifest.json version to match add-on config.json
- Add CI/CD auto-bump: patch version increments after every green build

## 1.1.0
- Add one-click my.home-assistant.io badges to README
- Fix Dockerfile COPY path /app/homebox to /app/api (correct binary location)
- Add ca-certificates and tzdata runtime dependencies

## 1.0.0
- Initial release: HA Supervisor add-on running Homebox inventory server locally
- Custom HA integration with conversation agent for natural-language inventory queries
- Location/room queries, keyword fallback search
- Lovelace card YAML example
- 50-test pytest suite (no HA install required)
- GitHub Actions CI: validate JSON, ruff lint, pytest
