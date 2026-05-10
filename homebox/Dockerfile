ARG BUILD_FROM
# Use the official Homebox image as base — avoids s6-overlay which requires
# true PID 1 and fails in LXC/Docker-in-Docker HA Supervisor installs.
FROM ghcr.io/sysadminsmedia/homebox:latest

RUN apk add --no-cache curl jq

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 7745

# run.sh execs /app/api as PID 1 — no init system needed
ENTRYPOINT ["/run.sh"]
