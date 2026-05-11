## 1.3.4
- **Fix: nginx `invalid number of the map parameters` crash on startup** —
  nginx's `map` directive does not support `$1` positional capture
  backreferences (those only work in `if` blocks and `rewrite` rules). Replaced
  the `map`-based cookie extraction with `set $hb_auth_token ""; if
  ($http_cookie ~ ...) { set $hb_auth_token $1; }` directly in the WebSocket
  location block. nginx now starts successfully and extracts the
  `hb.auth.token` cookie to inject as `?access_token=` for WS auth.

## 1.3.3
- **Fix: WebSocket 401 "authorization header or query is required"** — HA
  Supervisor's ingress proxy strips `Cookie` headers from WebSocket upgrade
  requests (a known Supervisor limitation). Homebox requires `hb.auth.token`
  cookie for WS auth but it never arrives. Fix: nginx `map` directive extracts
  the `hb.auth.token` cookie value from the full cookie string, then the
  dedicated `/api/v1/ws/` location injects it as `?access_token=TOKEN` query
  param — which Homebox accepts as an alternative auth mechanism. Regular HTTP
  requests continue to use cookie-based auth unaffected.
- **Fix: `proxy_buffering off` moved to WS-only location** — `sub_filter`
  requires buffering to scan response bodies. Previously `proxy_buffering off`
  was set server-wide, which could prevent sub_filter from working on large JS
  files. Now buffering is only disabled for the streaming WS location.

## 1.3.2
- **Fix: WebSocket `NS_ERROR_WEBSOCKET_CONNECTION_REFUSED`** — Homebox's frontend
  constructs the WS URL as `wss://${host}/api/v1/ws/events` using `window.location.host`
  directly, which bypasses the HA ingress path entirely. Patched the source at build
  time to use `wss://${host}/homebox/api/v1/ws/events` instead. The existing nginx
  `sub_filter '/homebox/' '%%INGRESS_ENTRY%%/'` rewrites this to the actual ingress
  path in the HTTP response, so the browser connects to the correct
  `wss://nabu.casa/api/hassio_ingress/TOKEN/api/v1/ws/events`.

## 1.3.1
- **Fix: `invalid storage path: not a subdirectory of base path`** — The new
  Homebox storage config uses `HBOX_STORAGE_CONN_STRING` (default `file:///./`,
  i.e. CWD) + `HBOX_STORAGE_PREFIX_PATH` (default `.data`). The app was running
  with CWD=`/`, resolving storage to `/.data` (invalid). Fixed by `cd /data/homebox`
  before starting the app, so all relative defaults resolve correctly. Also set
  `HBOX_DATABASE_SQLITE_PATH` explicitly to `/data/homebox/.data/homebox.db`.

## 1.3.0
- **Fix: `openssl: not found`** — Alpine doesn't include openssl by default;
  switched API key pepper generation to `head -c 48 /dev/urandom | base64`
  (uses only busybox built-ins, always available).
- **Fix: nginx 502 on first request** — nginx now starts AFTER Homebox is
  ready (polls `/api/v1/status` up to 30s), eliminating the race condition
  that caused immediate 502 errors on add-on start.

## 1.2.9
- **Fix: auto-generate `HBOX_AUTH_API_KEY_PEPPER` on first run** — Homebox requires
  a ≥32-byte pepper for API key signing. The add-on now auto-generates one via
  `openssl rand -base64 48` and persists it in `/data/homebox/.api_key_pepper` so
  API keys survive container restarts. No manual configuration required.

## 1.2.8
- **Fix: ARM64 binary was STILL x86-64 — switched to native arm64 CI runners** —
  The cross-compilation approach was fundamentally broken: BuildKit cached the
  `backend-builder` stage across platforms (both amd64 and arm64 builds used the
  same `GOARCH=amd64` layer). Root cause: `${TARGETARCH}` ARG was not being injected
  separately per platform in stages using `--platform=${BUILDPLATFORM}`. Switched to
  GitHub's native `ubuntu-24.04-arm` runner (free for public repos) — each platform
  now builds its own image natively (no QEMU, no cross-compilation), then a
  `docker buildx imagetools create` merge step creates the final multi-arch manifest.

## 1.2.7
- **Fix: ARM64 binary was actually x86-64 (root cause found)** — Homebox uses
  `gen2brain/{avif,heic,jpegxl,webp}` which are CGO packages (C bindings). Setting
  `CGO_ENABLED=0` without `-tags purego` silently fell back to native amd64 compilation
  instead of cross-compiling for arm64. The arm64 image manifest existed but contained
  an x86-64 ELF binary. Fixed by adding `-tags purego` to the Go build command, which
  forces all gen2brain packages to use their pure-Go/WASM (wazero) implementations,
  removing all CGO dependencies and enabling genuine static cross-compilation.

## 1.2.6
- **Fix: GHCR package visibility** — `GITHUB_TOKEN` in CI cannot change package
  visibility (GitHub limitation). CI now uses `GHCR_PAT` secret (a Personal Access
  Token with `write:packages` scope) for the visibility step. Until `GHCR_PAT` is
  added, the step logs a warning with the manual URL. **One-time manual step required:**
  set the package to public at the GHCR settings page.

## 1.2.5
- **Fix: GHCR image was inaccessible (private package)** — The nested image path
  `ghcr.io/amantux/ha-homebox-addon/homebox` caused the GitHub API visibility call
  to return HTTP 404 (slash in package name breaks the REST endpoint). Renamed image
  to `ghcr.io/amantux/ha-homebox-addon` (flat name) so the visibility PATCH succeeds
  automatically after every CI publish.

- **Fix: ARM64 binary execution failure** — Added explicit `chmod +x /app/api` in
  Dockerfile (belt-and-suspenders; Go build sets it, but COPY may not always preserve
  it). Added `file` utility to runtime image and diagnostic log line at startup showing
  host arch and binary type — makes future arch mismatches immediately diagnosable.

## 1.2.4
- **Fix: Docker image now actually published to GHCR** — GitHub Actions intentionally
  does not trigger new workflow runs when `GITHUB_TOKEN` pushes a commit. The previous
  design pushed a bump commit and waited for a second CI run to publish; that second
  run never fired. Fixed by running `publish` in the **same** CI workflow as
  `bump-version`, using the new version from the bump step's output. Every push to
  master now: validates → bumps version → builds and pushes the multi-arch image.

## 1.2.3
- Version bump (CI test of publish pipeline — publish job did not fire due to
  GITHUB_TOKEN push limitation; fixed in 1.2.4).

## 1.2.2
- **Fix: HA Supervisor could not build the image** — the 4-stage from-source
  Dockerfile (git clone + pnpm install + go build) requires internet access,
  substantial RAM, and ~10 minutes to complete. HA Supervisor's Docker builder
  runs inside a constrained environment and fails with "unknown error".

  Fix: CI (GitHub Actions) now builds the image and pushes it to
  `ghcr.io/amantux/ha-homebox-addon/homebox`. The add-on `config.json` now
  includes `"image": "ghcr.io/amantux/ha-homebox-addon/homebox"` so HA
  Supervisor pulls the pre-built image from the registry instead of building
  locally. Installation is now fast (~30 s) with no local compilation.

- Multi-arch support: CI builds `linux/amd64` and `linux/arm64` (aarch64) using
  Docker buildx with cross-compilation (Go native cross-compile; Node.js output
  is arch-agnostic). QEMU is only used for the final Alpine runtime layer.

- Removed `armv7` from supported architectures list (add-on now requires a
  64-bit OS on Raspberry Pi; all RPi 3B+ and newer support 64-bit HA OS).

## 1.2.1
- Go toolchain bumped to `golang:1.26-alpine` — Homebox `go.mod` now requires
  `go >= 1.26.0` (was using `golang:1.23` which rejected the build).


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
