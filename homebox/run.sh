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
export HBOX_LOG_LEVEL="${HBOX_LOG_LEVEL:-info}"

# Homebox uses file:///./  (cwd-relative) for storage by default.
# Set cwd to the data dir so all relative paths resolve correctly.
DATA_DIR="/data/homebox"
mkdir -p "${DATA_DIR}" /run/nginx
cd "${DATA_DIR}"

# SQLite DB path (explicit so it's always in our data dir)
export HBOX_DATABASE_SQLITE_PATH="${DATA_DIR}/.data/homebox.db?_pragma=busy_timeout=999&_pragma=journal_mode=WAL&_fk=1&_time_format=sqlite"

# ---------------------------------------------------------------------------
# Ensure HBOX_AUTH_API_KEY_PEPPER is set (required by Homebox ≥ 32 bytes).
# Persist it in /data so rotating the container never invalidates API keys.
# ---------------------------------------------------------------------------
PEPPER_FILE="${DATA_DIR}/.api_key_pepper"
if [ -z "${HBOX_AUTH_API_KEY_PEPPER:-}" ]; then
    if [ -f "${PEPPER_FILE}" ]; then
        HBOX_AUTH_API_KEY_PEPPER=$(cat "${PEPPER_FILE}")
        echo "[homebox] Loaded existing API key pepper from ${PEPPER_FILE}"
    else
        HBOX_AUTH_API_KEY_PEPPER=$(head -c 48 /dev/urandom | base64)
        echo "${HBOX_AUTH_API_KEY_PEPPER}" > "${PEPPER_FILE}"
        chmod 600 "${PEPPER_FILE}"
        echo "[homebox] Generated new API key pepper (stored in ${PEPPER_FILE})"
    fi
fi
export HBOX_AUTH_API_KEY_PEPPER

# ---------------------------------------------------------------------------
# Build nginx config from template, substituting runtime ingress values.
# If INGRESS_ENTRY is empty (standalone mode), sub_filter rules become no-ops.
# ---------------------------------------------------------------------------
sed \
    -e "s|%%INGRESS_PORT%%|${INGRESS_PORT}|g" \
    -e "s|%%INGRESS_ENTRY%%|${INGRESS_ENTRY}|g" \
    /etc/nginx/nginx.conf.tpl > /etc/nginx/nginx.conf

echo "[homebox] Starting Homebox on internal port ${HBOX_WEB_PORT}..."
echo "[homebox] host arch: $(uname -m) | binary: $(file /app/api 2>/dev/null | cut -d, -f1 || echo unknown)"
/app/api &
HBOX_PID=$!

# Wait for Homebox to be ready before starting nginx (avoids 502 on first request)
echo "[homebox] Waiting for Homebox to be ready..."
for i in $(seq 1 30); do
    if wget -qO- http://127.0.0.1:${HBOX_WEB_PORT}/api/v1/status >/dev/null 2>&1; then
        echo "[homebox] Homebox is ready"
        break
    fi
    sleep 1
done

echo "[homebox] nginx: ingress_port=${INGRESS_PORT} entry=${INGRESS_ENTRY:-<none>}"
echo "[homebox] Starting nginx..."
nginx &

# Keep container alive — exit if Homebox exits
wait $HBOX_PID
