## 1.1.7
- Fix sidebar ingress: removed ports/ports_description conflict with ingress: true
  (Supervisor was trying to bind the same port twice, ingress route lost)
- Fix changelog not showing in HA: moved CHANGELOG.md into add-on subdirectory
  (Supervisor only reads <addon_dir>/CHANGELOG.md, not the repo root)

## 1.1.6
- Fix sidebar not working: use INGRESS_PORT env var injected by Supervisor
  instead of hardcoded port 7745
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
