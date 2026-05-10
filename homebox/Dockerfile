ARG BUILD_FROM
# Use the official Homebox image as base — avoids s6-overlay which requires
# true PID 1 and fails in LXC/Docker-in-Docker HA Supervisor installs.
FROM ghcr.io/sysadminsmedia/homebox:latest

RUN apk add --no-cache curl jq nginx

# nginx config template — placeholders replaced at container startup by run.sh
COPY nginx.conf.tpl /etc/nginx/nginx.conf.tpl

COPY run.sh /run.sh
RUN chmod +x /run.sh && mkdir -p /run/nginx

# nginx listens on ingress_port (8099); Homebox listens on 7745 (loopback only)
EXPOSE 8099

# run.sh: configures nginx from template, starts nginx in background, execs /app/api
ENTRYPOINT ["/run.sh"]
