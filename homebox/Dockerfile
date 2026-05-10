ARG BUILD_FROM
FROM ${BUILD_FROM}

# Runtime dependencies
RUN apk add --no-cache ca-certificates tzdata

# Copy self-contained Homebox binary from official image
COPY --from=ghcr.io/sysadminsmedia/homebox:latest /app/api /homebox

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 7745

CMD ["/run.sh"]
