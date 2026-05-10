#!/bin/sh
set -e

# ---------------------------------------------------------------------------
# Read config from HA Supervisor API (SUPERVISOR_TOKEN is injected when
# hassio_api: true is set in config.json). Falls back to env/defaults.
# ---------------------------------------------------------------------------
if [ -n "${SUPERVISOR_TOKEN:-}" ]; then
    CONFIG=$(curl -sf \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        http://supervisor/addons/self/options/config 2>/dev/null || echo "{}")
    ADDON_TZ=$(echo "$CONFIG"       | jq -r '.timezone  // empty' 2>/dev/null)
    ADDON_LOG=$(echo "$CONFIG"      | jq -r '.log_level // empty' 2>/dev/null)
    TZ="${ADDON_TZ:-${TZ:-UTC}}"
    HBOX_LOG_LEVEL="${ADDON_LOG:-${HBOX_LOG_LEVEL:-info}}"
fi

export TZ="${TZ:-UTC}"
export HBOX_MODE="${HBOX_MODE:-production}"
# Use INGRESS_PORT injected by HA Supervisor when running behind ingress;
# fall back to 7745 for standalone / direct-access use.
export HBOX_WEB_PORT="${INGRESS_PORT:-${HBOX_WEB_PORT:-7745}}"
export HBOX_WEB_HOST="${HBOX_WEB_HOST:-0.0.0.0}"
export HBOX_STORAGE_DATA="${HBOX_STORAGE_DATA:-/data/homebox}"
export HBOX_LOG_LEVEL="${HBOX_LOG_LEVEL:-info}"

mkdir -p "${HBOX_STORAGE_DATA}"

echo "[homebox] Starting on port ${HBOX_WEB_PORT} (TZ=${TZ}, log=${HBOX_LOG_LEVEL})"

exec /app/api
