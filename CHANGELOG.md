# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
