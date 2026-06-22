/* Shared client helpers — auth token, API wrapper, formatting. */
const TOKEN_KEY = "estate_token";
const USER_KEY  = "estate_user";

function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
function getToken() { return localStorage.getItem(TOKEN_KEY); }
function getUser()  { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } }
function logout()   { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); location.href = "/login"; }

/* Redirect to login if there's no token. Call on protected pages. */
function requireAuth() {
  if (!getToken()) { location.href = "/login"; return false; }
  return true;
}

/* Fetch wrapper that attaches the JWT and handles auth errors. */
async function api(path, options = {}) {
  const opts = { ...options, headers: { ...(options.headers || {}) } };
  const token = getToken();
  if (token) opts.headers["Authorization"] = "Bearer " + token;
  if (opts.body && !(opts.body instanceof FormData)) {
    opts.headers["Content-Type"] = "application/json";
  }
  const res = await fetch(path, opts);
  if (res.status === 401) { logout(); throw new Error("Session expired"); }
  if (!res.ok) {
    let msg = "Request failed";
    try { const d = await res.json(); msg = d.detail || msg; } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

/* Sign in with Google (Google Identity Services).
   Fetches the client ID from the backend, renders the official button into
   `containerId`, and on success exchanges the Google credential for an app
   session, then redirects to the dashboard. `onError(msg)` is optional. */
async function setupGoogleSignIn(containerId, onError) {
  const container = document.getElementById(containerId);
  if (!container) return;
  let clientId = "";
  try {
    const cfg = await api("/api/config");
    clientId = cfg.google_client_id;
  } catch { /* ignore — handled below */ }
  if (!clientId) { container.style.display = "none"; return; }

  function ready() {
    /* global google */
    google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response) => {
        try {
          const data = await api("/api/auth/google", {
            method: "POST",
            body: JSON.stringify({ credential: response.credential }),
          });
          saveSession(data.access_token, data.user);
          location.href = "/dashboard";
        } catch (e) {
          if (onError) onError(e.message);
        }
      },
    });
    google.accounts.id.renderButton(container, {
      theme: "outline", size: "large", width: 320, text: "continue_with",
    });
  }

  if (window.google && google.accounts) ready();
  else {
    const wait = setInterval(() => {
      if (window.google && google.accounts) { clearInterval(wait); ready(); }
    }, 100);
  }
}

/* Formatting */
function inr(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN");
}
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function initials(name) {
  return String(name || "?").trim().split(/\s+/).map(w => w[0]).slice(0, 2).join("").toUpperCase();
}
function statusClass(s) { return "s-" + String(s || "").toLowerCase(); }
