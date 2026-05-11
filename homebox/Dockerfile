# ── Stage 1: Clone Homebox source ────────────────────────────────────────────
FROM alpine:3.20 AS source
RUN apk add --no-cache git
RUN git clone --depth 1 https://github.com/sysadminsmedia/homebox.git /src

# ── Stage 2: Build Nuxt frontend with /homebox/ base URL baked in ──────────
# JS output is architecture-agnostic; runs natively on whatever the CI runner is.
# NUXT_APP_BASE_URL bakes /homebox/ into every asset path and Vue Router base
# so a single nginx sub_filter handles path rewriting at runtime.
FROM node:22-alpine AS frontend-builder
ENV NUXT_APP_BASE_URL=/homebox/
WORKDIR /app
COPY --from=source /src/frontend/ .
COPY patches/use-server-events.patch.js /tmp/use-server-events.patch.js
# Patch WebSocket URL builder:
#  1. Bake /homebox/ into the WS path (nginx sub_filter rewrites to ingress entry at runtime)
#  2. Read hb.auth.ws_token (non-HttpOnly cookie set by patched backend) and append
#     ?access_token=TOKEN — bypasses HA Supervisor stripping Cookie on WS upgrades.
RUN node /tmp/use-server-events.patch.js composables/use-server-events.ts
RUN npm install -g pnpm \
    && pnpm install --frozen-lockfile \
    && pnpm build

# ── Stage 3: Build Go backend (native — no cross-compilation) ───────────────
# Built natively on the CI runner's arch (amd64 on ubuntu-latest,
# arm64 on ubuntu-24.04-arm). -tags purego forces gen2brain/{avif,heic,
# jpegxl,webp} to use their pure-Go/WASM (wazero) implementations instead
# of CGO C library bindings, so CGO_ENABLED=0 produces a fully static binary.
FROM golang:1.26-alpine AS backend-builder
RUN apk add --no-cache ca-certificates
WORKDIR /src
COPY --from=source /src/backend/ ./backend/
# Patch backend: add non-HttpOnly hb.auth.ws_token cookie alongside hb.auth.token.
# HA Supervisor strips Cookie headers from WebSocket upgrade requests, so the normal
# HttpOnly session cookie never arrives at Homebox for WS auth.
# The frontend (patched above) reads hb.auth.ws_token from document.cookie and sends
# it as ?access_token= in the WS URL, which mwAuthToken accepts as valid auth.
RUN awk '/\t\/\/ Set Fake Session cookie/{
    print "\t// Non-HttpOnly ws_token for WebSocket auth through HA Supervisor ingress."
    print "\t// HA Supervisor strips Cookie headers from WS upgrade requests; JS reads"
    print "\t// this cookie and appends it as ?access_token= to the WebSocket URL."
    print "\thttp.SetCookie(w, \&http.Cookie{"
    print "\t\tName:     \"hb.auth.ws_token\","
    print "\t\tValue:    token,"
    print "\t\tPath:     \"/\","
    print "\t\tDomain:   domain,"
    print "\t\tExpires:  expires,"
    print "\t\tHttpOnly: false,"
    print "\t\tSameSite: http.SameSiteStrictMode,"
    print "\t})"
}{ print }' \
    backend/app/api/handlers/v1/v1_ctrl_auth.go \
    > /tmp/v1_ctrl_auth_patched.go \
    && mv /tmp/v1_ctrl_auth_patched.go backend/app/api/handlers/v1/v1_ctrl_auth.go
RUN rm -rf ./backend/app/api/static/public
COPY --from=frontend-builder /app/.output/public/ ./backend/app/api/static/public/
WORKDIR /src/backend
RUN echo "Building for: $(go env GOOS)/$(go env GOARCH)" && \
    CGO_ENABLED=0 \
    go build -tags purego -ldflags="-s -w" -o /app/api ./app/api/

# ── Stage 4: Minimal runtime image ───────────────────────────────────────────
FROM alpine:3.20
RUN apk add --no-cache curl jq nginx tzdata ca-certificates file

COPY --from=backend-builder /app/api /app/api
COPY nginx.conf.tpl /etc/nginx/nginx.conf.tpl
COPY run.sh /run.sh
RUN chmod +x /run.sh /app/api \
    && file /app/api \
    && mkdir -p /run/nginx /data/homebox

# nginx listens on ingress_port (8099); Homebox listens on 7745 (loopback only)
EXPOSE 8099

# run.sh reads ingress config from Supervisor API, renders nginx template,
# starts nginx in background, then exec's Homebox as PID 1.
ENTRYPOINT ["/run.sh"]
