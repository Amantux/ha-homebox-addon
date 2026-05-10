#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: Homebox
# Starts the Homebox inventory management server
# ==============================================================================

# Read config options
TIMEZONE=$(bashio::config 'timezone')
LOG_LEVEL=$(bashio::config 'log_level')

# Apply timezone
export TZ="${TIMEZONE}"

# Homebox environment configuration
export HBOX_MODE="production"
export HBOX_WEB_PORT=7745
export HBOX_WEB_HOST="0.0.0.0"
export HBOX_STORAGE_DATA="/data/homebox"
export HBOX_LOG_LEVEL="${LOG_LEVEL}"

# Ensure data directory exists
mkdir -p /data/homebox

bashio::log.info "Starting Homebox on port 7745..."
bashio::log.info "Data directory: /data/homebox"
bashio::log.info "Timezone: ${TIMEZONE}"

exec /usr/bin/homebox
