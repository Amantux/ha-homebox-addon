# Inserts a non-HttpOnly hb.auth.ws_token cookie alongside hb.auth.token in
# Homebox's setCookies function.
#
# HA Supervisor strips Cookie headers from WebSocket upgrade requests before
# they reach the container. The patched frontend reads hb.auth.ws_token from
# document.cookie (readable because HttpOnly=false) and appends it as
# ?access_token=TOKEN to the WebSocket URL. Homebox's mwAuthToken middleware
# already accepts the access_token query parameter as a valid auth mechanism.
#
# Anchor: "Set attachment token cookie (accessible to frontend, not HttpOnly)"
# This comment appears ONLY in setCookies (not in unsetCookies), making it a
# safe unique insertion point. The new cookie is inserted before it.
#
# Usage: awk -f backend-ws-token.awk v1_ctrl_auth.go > patched.go
/\t\/\/ Set attachment token cookie \(accessible to frontend, not HttpOnly\)/ {
    print "\t// Non-HttpOnly ws_token for WebSocket auth through HA Supervisor ingress."
    print "\t// HA Supervisor strips Cookie headers from WS upgrade requests; the"
    print "\t// patched frontend reads this cookie and sends it as ?access_token=."
    print "\thttp.SetCookie(w, &http.Cookie{"
    print "\t\tName:     \"hb.auth.ws_token\","
    print "\t\tValue:    token,"
    print "\t\tPath:     \"/\","
    print "\t\tDomain:   domain,"
    print "\t\tExpires:  expires,"
    print "\t\tSecure:   ctrl.cookieSecure,"
    print "\t\tHttpOnly: false,"
    print "\t\tSameSite: http.SameSiteLaxMode,"
    print "\t})"
    print ""
}
{ print }
