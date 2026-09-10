// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Log in and open a session
// category: Connection & session
// id:       connection.login

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

// connect() is preloaded by the playground; in the browser the call goes
// to the playground backend, which forwards the RPC (or answers from mock
// data). login:false lets us call login() ourselves below and handle a failure.
const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS, login: false });

try {
  const user = await elo.login();  // -> POST /api/elo/proxy -> IX login
  console.log("logged in as:", user.name, `(id ${user.id})`);
  console.log("member of groups:", user.groupList);
} catch (exc) {
  const msg = (exc && exc.message) || String(exc);
  if (/ELOIX:3008|authentication failed|HTTP 401|HTTP 403/.test(msg)) {
    console.log("login failed: wrong user or password -", msg);
  } else if (/request failed|fetch failed|Failed to fetch|NetworkError/.test(msg)) {
    console.log("login failed: cannot reach the server -", msg);
  } else if (/HTTP 404/.test(msg)) {
    console.log("login failed: the repository path in ELO_BASE_URL looks wrong -", msg.split(" - ")[0]);
  } else {
    console.log("login failed:", msg);
  }
}
