#!/bin/sh
set -e

# ---------------------------------------------------------------------------
# Read add-on options and ingress config from HA Supervisor API.
# SUPERVISOR_TOKEN is injected when hassio_api: true is set in config.json.
# INGRESS_PORT is NOT injected by Supervisor — we read it from the API.
# ---------------------------------------------------------------------------
INGRESS_PORT="8099"
INGRESS_ENTRY=""

if [ -n "${SUPERVISOR_TOKEN:-}" ]; then
    CONFIG=$(curl -sf \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        http://supervisor/addons/self/options/config 2>/dev/null || echo "{}")
    INFO=$(curl -sf \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        http://supervisor/addons/self/info 2>/dev/null || echo '{"data":{}}')

    ADDON_TZ=$(echo "$CONFIG" | jq -r '.timezone  // empty' 2>/dev/null)
    ADDON_LOG=$(echo "$CONFIG" | jq -r '.log_level // empty' 2>/dev/null)

    # ingress_port: the port Supervisor proxies to on this container
    # ingress_entry: full path prefix e.g. /api/hassio_ingress/abc123TOKEN
    INGRESS_PORT=$(echo "$INFO"  | jq -r '.data.ingress_port  // "8099"' 2>/dev/null)
    INGRESS_ENTRY=$(echo "$INFO" | jq -r '.data.ingress_entry // ""'     2>/dev/null)

    TZ="${ADDON_TZ:-${TZ:-UTC}}"
    HBOX_LOG_LEVEL="${ADDON_LOG:-${HBOX_LOG_LEVEL:-info}}"
fi

export TZ="${TZ:-UTC}"
export HBOX_MODE="${HBOX_MODE:-production}"
export HBOX_WEB_PORT="7745"           # Fixed internal port — nginx proxies to us
export HBOX_WEB_HOST="127.0.0.1"     # Loopback only — not directly reachable
export HBOX_STORAGE_DATA="${HBOX_STORAGE_DATA:-/data/homebox}"
export HBOX_LOG_LEVEL="${HBOX_LOG_LEVEL:-info}"

mkdir -p "${HBOX_STORAGE_DATA}" /run/nginx

# ---------------------------------------------------------------------------
# Build nginx config from template, substituting runtime ingress values.
# If INGRESS_ENTRY is empty (standalone mode), sub_filter rules become no-ops.
# ---------------------------------------------------------------------------
sed \
    -e "s|%%INGRESS_PORT%%|${INGRESS_PORT}|g" \
    -e "s|%%INGRESS_ENTRY%%|${INGRESS_ENTRY}|g" \
    /etc/nginx/nginx.conf.tpl > /etc/nginx/nginx.conf

echo "[homebox] nginx: ingress_port=${INGRESS_PORT} entry=${INGRESS_ENTRY:-<none>}"
echo "[homebox] Starting nginx..."
nginx &

sleep 1

echo "[homebox] Starting Homebox on internal port ${HBOX_WEB_PORT}..."
exec /app/api
