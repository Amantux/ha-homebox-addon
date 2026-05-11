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

        # ── WebSocket endpoint ───────────────────────────────────────────────
        # Separate location so we can:
        #  1. Disable proxy_buffering (required for streaming WS frames)
        #  2. Inject access_token query param from cookie (bypasses Supervisor
        #     stripping Cookie headers on WS upgrade requests)
        location ~ ^/api/v1/ws/ {
            # Extract hb.auth.token cookie using if/regex ($1 capture works here).
            # HA Supervisor strips Cookie headers from WS upgrade requests, so
            # cookie-based auth never reaches Homebox. Inject as ?access_token=.
            set $hb_auth_token "";
            if ($http_cookie ~ "(?:^|;\s*)hb\.auth\.token=([^;]+)") {
                set $hb_auth_token $1;
            }

            proxy_pass         http://127.0.0.1:7745$uri?access_token=$hb_auth_token&$args;
            proxy_http_version 1.1;
            proxy_set_header   Upgrade           $http_upgrade;
            proxy_set_header   Connection        $connection_upgrade;
            proxy_set_header   Host              $http_host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_set_header   Cookie            $http_cookie;
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;
            proxy_buffering    off;
        }

        # ── All other requests ───────────────────────────────────────────────
        location / {
            proxy_pass         http://127.0.0.1:7745;
            proxy_http_version 1.1;

            proxy_set_header   Upgrade    $http_upgrade;
            proxy_set_header   Connection $connection_upgrade;
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;

            proxy_set_header   Host              $http_host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_set_header   Cookie            $http_cookie;

            # Strip Homebox's X-Frame-Options: DENY so HA can embed in its iframe.
            proxy_hide_header X-Frame-Options;
            proxy_hide_header Content-Security-Policy;
            add_header X-Frame-Options "SAMEORIGIN" always;

            # Disable upstream gzip so sub_filter reads plain text.
            proxy_set_header   Accept-Encoding   "";

            # Rewrite Location headers on 302 redirects.
            absolute_redirect  off;
            proxy_redirect     /homebox/ %%INGRESS_ENTRY%%/;
            proxy_redirect     / %%INGRESS_ENTRY%%/;

            sub_filter_once off;
            sub_filter_types *;

            # /set-theme.js is hardcoded absolute in nuxt.config.ts app.head.
            sub_filter 'src="/set-theme.js"' 'src="/homebox/set-theme.js"';

            # JS fetch/useFetch calls use absolute /api/ paths.
            sub_filter '"/api/'  '"/homebox/api/';
            sub_filter "'/api/"  "'/homebox/api/";
            sub_filter '`/api/'  '`/homebox/api/';

            # Main rewrite: /homebox/ → actual ingress entry.
            sub_filter '/homebox/' '%%INGRESS_ENTRY%%/';
        }
    }
}

