ARG BUILD_FROM

# ── Stage 1: Clone Homebox source ──────────────────────────────────────────
# Shallow clone of the default branch (matches ghcr.io/sysadminsmedia/homebox:latest)
FROM alpine:3.20 AS source
RUN apk add --no-cache git
RUN git clone --depth 1 https://github.com/sysadminsmedia/homebox.git /src

# ── Stage 2: Build Nuxt frontend with /homebox/ base URL baked in ──────────
# NUXT_APP_BASE_URL is a first-class Nuxt 3 env var that sets app.baseURL at
# build time.  Every /_nuxt/ asset path and the Vue Router base become
# /homebox/_nuxt/... in the compiled output.  At runtime, a single nginx
# sub_filter rewrites /homebox/ → the real HA ingress entry.
FROM node:22-alpine AS frontend-builder
ENV NUXT_APP_BASE_URL=/homebox/
WORKDIR /app
COPY --from=source /src/frontend/ .
RUN npm install -g pnpm \
    && pnpm install --frozen-lockfile \
    && pnpm build

# ── Stage 3: Build Go backend (embeds frontend static files) ───────────────
FROM golang:1.26-alpine AS backend-builder
RUN apk add --no-cache ca-certificates
WORKDIR /src
COPY --from=source /src/backend/ ./backend/
# Replace the placeholder static/public directory with our custom-built frontend
RUN rm -rf ./backend/app/api/static/public
COPY --from=frontend-builder /app/.output/public/ ./backend/app/api/static/public/
WORKDIR /src/backend
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/api ./app/api/

# ── Stage 4: Minimal runtime image ─────────────────────────────────────────
FROM alpine:3.20
RUN apk add --no-cache curl jq nginx tzdata ca-certificates

COPY --from=backend-builder /app/api /app/api
COPY nginx.conf.tpl /etc/nginx/nginx.conf.tpl
COPY run.sh /run.sh
RUN chmod +x /run.sh && mkdir -p /run/nginx /data/homebox

# nginx listens on ingress_port (8099); Homebox listens on 7745 (loopback only)
EXPOSE 8099

# run.sh: reads ingress config from Supervisor API, renders nginx template,
# starts nginx in background, then exec's Homebox as PID 1.
ENTRYPOINT ["/run.sh"]
