ARG BUILD_FROM
FROM ${BUILD_FROM}

COPY --from=homebox/homebox:latest /homebox /homebox

RUN apk add --no-cache python3 py3-pip
RUN pip install --no-cache-dir flask flask-sqlalchemy

COPY addon/chat_bridge.py /app/chat_bridge.py
COPY addon/run.sh /run.sh
RUN chmod +x /run.sh

WORKDIR /
EXPOSE 80 8081

ENTRYPOINT ["/run.sh"]
