ARG BUILD_FROM
FROM ${BUILD_FROM}

# Runtime dependencies
RUN apk add --no-cache ca-certificates tzdata

# Copy self-contained Homebox binary from official image
COPY --from=ghcr.io/sysadminsmedia/homebox:latest /app/api /usr/bin/homebox

# Register as an s6 service (HA base image uses s6-overlay as PID 1)
COPY run.sh /etc/services.d/homebox/run
RUN chmod a+x /etc/services.d/homebox/run

EXPOSE 7745
