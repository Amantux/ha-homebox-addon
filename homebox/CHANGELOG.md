## 1.1.8
- Fix sidebar/ingress: add nginx sidecar proxy with sub_filter path rewriting
  Homebox's Nuxt SPA bakes absolute asset paths (/_nuxt/...) into the binary.
  The browser resolves these against the HA origin root, bypassing the ingress
  proxy. nginx rewrites all /_nuxt/, /api/v1, /set-theme.js paths to include
  the full ingress entry prefix before they reach the browser.
- ingress_port changed from 7745 to 8099 (nginx listens here; Homebox internal)
- Homebox now bound to 127.0.0.1:7745 (loopback only, not directly reachable)
- Ingress entry and port read from Supervisor REST API at container startup

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
