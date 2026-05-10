daemon off;
user root;
pid /run/nginx.pid;
worker_processes auto;
error_log /proc/1/fd/1 error;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;
    access_log    /proc/1/fd/1;

    map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }

    server {
        listen 0.0.0.0:%%INGRESS_PORT%% default_server;
        server_name _;
        client_max_body_size 0;
        proxy_buffering off;

        location / {
            proxy_pass         http://127.0.0.1:7745;
            proxy_http_version 1.1;

            # WebSocket / SSE support
            proxy_set_header   Upgrade    $http_upgrade;
            proxy_set_header   Connection $connection_upgrade;
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;

            # Standard proxy headers
            proxy_set_header   Host              $http_host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_set_header   X-Ingress-Path    "%%INGRESS_ENTRY%%";

            # CRITICAL: strip Homebox's X-Frame-Options: DENY so HA can embed in iframe.
            # Both the HA dashboard and the ingress URL share the same origin
            # (e.g. v4qwgan6....ui.nabu.casa), so SAMEORIGIN is safe and sufficient.
            proxy_hide_header X-Frame-Options;
            proxy_hide_header Content-Security-Policy;
            add_header X-Frame-Options "SAMEORIGIN" always;

            # CRITICAL: disable upstream compression so sub_filter can read plain text
            proxy_set_header   Accept-Encoding   "";

            # Rewrite Location: redirect headers from Homebox
            absolute_redirect  off;
            proxy_redirect     / %%INGRESS_ENTRY%%/;

            # ── Rewrite baked-in absolute asset paths ────────────────────
            # Apply to every occurrence in every content type
            sub_filter_once off;
            sub_filter_types *;

            # HTML <link href> and <script src> pointing at /_nuxt/ chunks
            sub_filter 'href="/_nuxt/'   'href="%%INGRESS_ENTRY%%/_nuxt/';
            sub_filter 'src="/_nuxt/'    'src="%%INGRESS_ENTRY%%/_nuxt/';

            # Nuxt head script injected by nuxt.config.ts: { src: "/set-theme.js" }
            sub_filter '"/set-theme.js"'  '"%%INGRESS_ENTRY%%/set-theme.js"';
            sub_filter "'/set-theme.js'"  "'%%INGRESS_ENTRY%%/set-theme.js'";

            # /_nuxt/builds/ manifest references
            sub_filter '"/_nuxt/builds/'  '"%%INGRESS_ENTRY%%/_nuxt/builds/';

            # JavaScript API calls — all quote/template-literal styles
            sub_filter '"/api/v1'    '"%%INGRESS_ENTRY%%/api/v1';
            sub_filter "'/api/v1"    "'%%INGRESS_ENTRY%%/api/v1";
            sub_filter '`/api/v1'    '`%%INGRESS_ENTRY%%/api/v1';

            # fetch() and EventSource() calls
            sub_filter 'fetch("/'         'fetch("%%INGRESS_ENTRY%%/';
            sub_filter "fetch('/"         "fetch('%%INGRESS_ENTRY%%/";
            sub_filter 'EventSource("/'   'EventSource("%%INGRESS_ENTRY%%/';
            sub_filter "EventSource('/"   "EventSource('%%INGRESS_ENTRY%%/";
        }
    }
}
