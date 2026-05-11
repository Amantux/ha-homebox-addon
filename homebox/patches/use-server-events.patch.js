#!/usr/bin/env node
// Patches frontend/composables/use-server-events.ts for HA Supervisor ingress.
//
// Problems fixed:
//   1. WS URL uses bare /api/v1/ws/events — bypasses the ingress path prefix.
//      Fix: bake /homebox/ into the path (nginx sub_filter rewrites it at runtime
//           to the actual ingress entry point).
//
//   2. HA Supervisor strips Cookie headers from WebSocket upgrade requests, so
//      Homebox never receives hb.auth.token and returns 401.
//      Fix: backend now also sets hb.auth.ws_token (non-HttpOnly, readable by JS).
//           This script patches the WS URL builder to read that cookie and append
//           ?access_token=TOKEN so Homebox's mwAuthToken middleware accepts it.

const fs = require("fs");
const filePath = process.argv[2] || "composables/use-server-events.ts";

let src = fs.readFileSync(filePath, "utf8");

// ── Find the URL construction block ─────────────────────────────────────────
const oldBlock = `  let url = \`\${protocol}://\${host}/api/v1/ws/events\`;
  if (currentTenantId) {
    url += \`?tenant=\${currentTenantId}\`;
  }`;

const newBlock = `  // Read the non-HttpOnly ws_token cookie set by the patched Homebox backend.
  // HA Supervisor strips Cookie headers from WebSocket upgrade requests, so the
  // normal hb.auth.token (HttpOnly) session cookie never reaches Homebox for WS.
  // The backend sets hb.auth.ws_token as a non-HttpOnly copy so JS can read it
  // here and pass it as ?access_token= — which mwAuthToken accepts as valid auth.
  const wsToken = (() => {
    const m = document.cookie.match(/(?:^|;\\s*)hb\\.auth\\.ws_token=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  })();
  // /homebox/ is baked in so nginx sub_filter can rewrite it to the real ingress
  // entry path at response-serve time, giving the browser the correct WS URL.
  let url = \`\${protocol}://\${host}/homebox/api/v1/ws/events\`;
  const wsParams = new URLSearchParams();
  if (currentTenantId) wsParams.set("tenant", currentTenantId);
  if (wsToken) wsParams.set("access_token", wsToken);
  const wsQs = wsParams.toString();
  if (wsQs) url += "?" + wsQs;`;

if (!src.includes(oldBlock)) {
  console.error("ERROR: target block not found in", filePath);
  console.error("File may have already been patched or upstream changed.");
  process.exit(1);
}

src = src.replace(oldBlock, newBlock);
fs.writeFileSync(filePath, src);
console.log("Patched", filePath);
