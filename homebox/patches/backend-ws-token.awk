# Inserts a non-HttpOnly hb.auth.ws_token cookie alongside hb.auth.token in
# Homebox's setCookies function.
#
# HA Supervisor strips Cookie headers from WebSocket upgrade requests before
# they reach the container. The patched frontend reads hb.auth.ws_token from
# document.cookie (readable because HttpOnly=false) and appends it as
# ?access_token=TOKEN to the WebSocket URL. Homebox's mwAuthToken middleware
# already accepts the access_token query parameter as a valid auth mechanism.
#
# Usage: awk -f backend-ws-token.awk v1_ctrl_auth.go > patched.go
/\t\/\/ Set Fake Session cookie/ {
    print "\t// Non-HttpOnly ws_token for WebSocket auth through HA Supervisor ingress."
    print "\t// HA Supervisor strips Cookie headers from WS upgrade requests; the"
    print "\t// patched frontend reads this cookie and sends it as ?access_token=."
    print "\thttp.SetCookie(w, &http.Cookie{"
    print "\t\tName:     \"hb.auth.ws_token\","
    print "\t\tValue:    token,"
    print "\t\tPath:     \"/\","
    print "\t\tDomain:   domain,"
    print "\t\tExpires:  expires,"
    print "\t\tHttpOnly: false,"
    print "\t\tSameSite: http.SameSiteStrictMode,"
    print "\t})"
}
{ print }
