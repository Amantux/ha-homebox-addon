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
# Patch WebSocket URL to include /homebox/ base path.
# use-server-events.ts constructs `wss://${host}/api/v1/ws/events` at runtime,
# bypassing the HA ingress path. We bake /homebox/ into the path so the nginx
# sub_filter (which rewrites /homebox/ → actual ingress entry) fixes it at
# response time, giving the browser the correct ingress-prefixed WS URL.
RUN sed -i 's|${host}/api/v1/ws/events|${host}/homebox/api/v1/ws/events|g' \
    composables/use-server-events.ts
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
