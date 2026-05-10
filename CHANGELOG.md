# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] – 2026-05-10

### Changed — Architecture overhaul: build from source (proper ingress)

Previous versions used nginx `sub_filter` to pattern-match 12+ variations of `/_nuxt/` paths
in Homebox's minified JavaScript — a fragile approach that broke whenever Nuxt added a new path
format (e.g. `/_nuxt/builds/meta/`).

Research across official HA add-ons confirmed the correct approach (Mealie pattern):

1. **Build-time**: compile the Nuxt frontend with `NUXT_APP_BASE_URL=/homebox/` so every asset
   path and the Vue Router base are baked in as `/homebox/_nuxt/...` instead of `/_nuxt/...`.
2. **Runtime**: a single nginx `sub_filter '/homebox/' 'INGRESS_ENTRY/'` rewrites both asset
   URLs and the router base to the real HA ingress path in one pass.

Multi-stage Dockerfile:
- Stage 1 (`alpine`): shallow git clone of `sysadminsmedia/homebox`
- Stage 2 (`node:22-alpine`): `pnpm build` with `NUXT_APP_BASE_URL=/homebox/`
- Stage 3 (`golang:1.23-alpine`): `go build ./app/api/` with the custom frontend embedded
- Stage 4 (`alpine:3.20`): minimal runtime — nginx + binary only

nginx `sub_filter` rules reduced from 12 to 4. Dependency on the pre-built
`ghcr.io/sysadminsmedia/homebox:latest` image removed.

> First install builds from source (~10 min). Subsequent installs use Docker layer cache.

---

## [1.1.9] – 2026-05-10

### Fixed
- **Firefox "Can't Open This Page" / iframe blocked** — Homebox sends `X-Frame-Options: DENY`
  on every response. HA ingress embeds the add-on UI in a `<iframe>` in the sidebar. Browsers
  enforce `X-Frame-Options: DENY` and refuse to display the frame.
- Fix: nginx now strips the upstream header and responds with `X-Frame-Options: SAMEORIGIN`.
  `SAMEORIGIN` is correct because the parent (HA dashboard) and the iframe (ingress URL) share
  the same origin (e.g. the same Nabu Casa subdomain).
- Also strips upstream `Content-Security-Policy` which may additionally block framing.

---

## [1.1.8] – 2026-05-10

### Fixed
- **Sidebar / ingress frontend completely broken** — Root cause (confirmed by 4-expert debate
  + HA Supervisor source code analysis): Homebox's Nuxt SPA is compiled with all asset paths
  rooted at `/` (`/_nuxt/entry.js`, `/set-theme.js`, etc.). When served through the HA ingress
  proxy at `/api/hassio_ingress/{token}/`, the browser resolves those absolute paths against
  `https://ha-host:8123/` — entirely bypassing the ingress tunnel — so no JS/CSS loads.
- **Fix**: Added nginx sidecar proxy inside the container.  
  - nginx listens on `ingress_port` (8099) — the port Supervisor connects to.  
  - Homebox binds to `127.0.0.1:7745` (loopback only, not directly reachable).  
  - nginx uses `sub_filter` to rewrite `/_nuxt/`, `/api/v1`, `/set-theme.js`, etc. into
    `{ingress_entry}/_nuxt/`, `{ingress_entry}/api/v1` etc. before responses reach the browser.  
  - `ingress_entry` and `ingress_port` are read from Supervisor REST API at startup
    (using existing `SUPERVISOR_TOKEN`; no bashio required).
- **`INGRESS_PORT` myth busted**: Supervisor source (`supervisor/docker/addon.py`) only injects
  `TZ`, `SUPERVISOR_TOKEN`, and `HASSIO_TOKEN`. The port is read from the Supervisor API.

### Technical
- Pattern proven by Mealie (`alexbelgium/hassio-addons`) and BirdNET-Go add-ons
- `proxy_set_header Accept-Encoding ""` disables upstream gzip so `sub_filter` sees plain text
- `sub_filter_once off` + `sub_filter_types *` applies rewrites to all content types

---

## [1.1.7] – 2026-05-10

### Fixed
- **Sidebar ingress conflict** — `ports`/`ports_description` entries in `config.json`
  conflicted with `ingress: true`: Supervisor tried to bind the same port twice and
  the ingress route lost. Removed the `ports` block; ingress owns the networking.
- **Changelog not showing in HA** — HA Supervisor reads `<addon_dir>/CHANGELOG.md`
  (i.e., `homebox/CHANGELOG.md`), never the repo root. Created the file in the correct
  location with bare `## X.Y.Z` headers as required by the Supervisor's parser.
  Bracketed format `## [X.Y.Z]` is silently ignored by HA.

---

## [1.1.6] – 2026-05-10

### Fixed
- **Sidebar / ingress not working** — `run.sh` was hardcoding `HBOX_WEB_PORT=7745`
  and ignoring the `INGRESS_PORT` environment variable injected by HA Supervisor.
  When the Supervisor assigns a dynamic ingress port, Homebox was listening on the
  wrong port, so the sidebar panel showed a blank or unreachable page.
  Fixed by using `${INGRESS_PORT:-7745}` so the Supervisor's assigned port always wins.
- Added `ingress_stream: true` to `config.json` — required for WebSocket and
  streaming connections (used by Homebox's live UI) to pass through the HA ingress
  reverse proxy correctly.

---

## [1.1.5] – 2026-05-10

### Changed
- Version bump requested manually; no functional changes from 1.1.2.

> **Note:** versions 1.1.3 and 1.1.4 were skipped — the project went from 1.1.2
> directly to 1.1.5 at user request.

---

## [1.1.2] – 2026-05-10

### Fixed
- **Critical: s6-overlay PID 1 crash** — `s6-overlay-suexec: fatal: can only run as pid 1`
  was triggered in any HA Supervisor install that runs inside Docker, LXC, or Proxmox
  because the container's entrypoint was not guaranteed to be PID 1. Fixed by switching
  to the official Homebox image as the base and running `/app/api` directly as PID 1
  via a plain POSIX `sh` init script. s6-overlay is no longer involved.
- **run.sh** — replaced `bashio` dependency with a minimal POSIX shell script that reads
  add-on config from the Supervisor REST API (`/supervisor/addons/self/options/config`)
  using `curl` + `jq` when `SUPERVISOR_TOKEN` is available, falling back to env var
  defaults otherwise.

### Changed
- Dockerfile now builds `FROM ghcr.io/sysadminsmedia/homebox:latest` directly instead
  of copying the binary into an HA base image layer.
- `build.json` simplified — arch-specific HA base image mappings removed (Homebox
  official image is already multi-arch).
- `config.json` — added `hassio_api: true` and `hassio_role: "default"` so HA Supervisor
  injects `SUPERVISOR_TOKEN` for config reading.

---

## [1.1.1] – 2026-05-10

### Fixed
- Synced integration `manifest.json` version to match add-on `config.json` version
  (both now track the same number via the CI auto-bump job).

### Added
- CI/CD auto-bumps patch version in both `homebox/config.json` and
  `custom_components/homebox/manifest.json` after every successful push to master.

---

## [1.1.0] – 2026-05-10

### Added
- One-click `my.home-assistant.io` badges in README for add-on repository and
  integration config-flow setup.
- CI status, license, architecture, and HA integration/add-on shield badges.

### Fixed
- Dockerfile `COPY --from` path corrected from `/app/homebox` to `/app/api`
  (the actual binary path in the official Homebox image).
- `ca-certificates` and `tzdata` added as runtime dependencies.

---

## [1.0.0] – 2026-05-09

### Added
- **HA Supervisor Add-on** (`homebox/`) — runs Homebox inventory server locally with
  ingress support, port 7745, persistent `/data/homebox` storage, and timezone/log-level
  config options.
- **Custom HA Integration** (`custom_components/homebox/`) — conversation agent for
  natural-language inventory queries ("Where is my hammer?", "What's in the garage?").
- Location/room queries with partial name matching.
- Keyword fallback search for multi-word queries with no exact match.
- Lovelace card YAML example with search input, button, and result display.
- pytest test suite (50 tests, no HA install required).
- GitHub Actions CI — validate add-on JSON, ruff lint, pytest.
- Public repository with `repository.json` for HA add-on store registration.
