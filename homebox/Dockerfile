# buildx injects these automatically; declare before first FROM to use in FROM lines
ARG BUILDPLATFORM
ARG TARGETOS=linux
ARG TARGETARCH=amd64

# ── Stage 1: Clone Homebox source (always native — just downloading files) ──
FROM --platform=${BUILDPLATFORM} alpine:3.20 AS source
RUN apk add --no-cache git
RUN git clone --depth 1 https://github.com/sysadminsmedia/homebox.git /src

# ── Stage 2: Build Nuxt frontend with /homebox/ base URL baked in ──────────
# Runs native on the CI host (amd64). JS output is architecture-agnostic.
# NUXT_APP_BASE_URL bakes /homebox/ into every asset path and Vue Router base
# in the compiled JS so a single nginx sub_filter handles path rewriting.
FROM --platform=${BUILDPLATFORM} node:22-alpine AS frontend-builder
ENV NUXT_APP_BASE_URL=/homebox/
WORKDIR /app
COPY --from=source /src/frontend/ .
RUN npm install -g pnpm \
    && pnpm install --frozen-lockfile \
    && pnpm build

# ── Stage 3: Cross-compile Go backend (native, no QEMU) ────────────────────
# Go has first-class cross-compilation: GOOS/GOARCH produce the target binary
# on the build host without emulation. CGO disabled — modernc.org/sqlite is
# pure Go.
FROM --platform=${BUILDPLATFORM} golang:1.26-alpine AS backend-builder
ARG TARGETOS TARGETARCH
RUN apk add --no-cache ca-certificates
WORKDIR /src
COPY --from=source /src/backend/ ./backend/
RUN rm -rf ./backend/app/api/static/public
COPY --from=frontend-builder /app/.output/public/ ./backend/app/api/static/public/
WORKDIR /src/backend
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -ldflags="-s -w" -o /app/api ./app/api/

# ── Stage 4: Minimal runtime image (target platform) ───────────────────────
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

# run.sh: reads ingress config from Supervisor API, renders nginx template,
# starts nginx in background, then exec's Homebox as PID 1.
ENTRYPOINT ["/run.sh"]
