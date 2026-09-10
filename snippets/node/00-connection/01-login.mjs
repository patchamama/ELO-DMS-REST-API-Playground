// import the shared client:  import { connect } from "elo-playground";
// topic:    Log in and open a session
// category: Connection & session
// id:       connection.login

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

// login:false builds the client but does NOT log in yet, so we can call
// login() ourselves below, read what it returns and handle a failure.
const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS, login: false });

try {
  const user = await elo.login();  // -> POST /rest/IXServicePortIF/login
  console.log("logged in as:", user.name, `(id ${user.id})`);
  console.log("member of groups:", user.groupList);
} catch (exc) {
  if (!(exc instanceof EloError)) throw exc;
  const msg = exc.message;
  if (/ELOIX:3008|authentication failed|HTTP 401|HTTP 403/.test(msg)) {
    console.log("login failed: wrong user or password -", msg);
  } else if (/request failed/.test(msg)) {
    console.log("login failed: cannot reach the server, check the host/port in ELO_BASE_URL -", msg);
  } else if (/HTTP 404/.test(msg)) {
    console.log("login failed: the repository path in ELO_BASE_URL looks wrong -", msg.split(" - ")[0]);
  } else {
    console.log("login failed:", msg);
  }
} finally {
  elo.close();
}
