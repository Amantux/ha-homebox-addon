ARG BUILD_FROM
FROM ${BUILD_FROM}

# Copy Homebox binary from official image
COPY --from=ghcr.io/sysadminsmedia/homebox:latest /app/homebox /homebox

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 7745

CMD ["/run.sh"]
