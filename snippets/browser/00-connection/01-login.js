// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Log in and open a session
// category: Connection & session
// id:       connection.login

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

// connect() is preloaded by the playground; in the browser the call goes
// to the playground backend, which forwards the RPC (or answers from mock
// data). login:false lets us call login() ourselves below.
const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS, login: false });

const user = await elo.login();    // -> POST /api/elo/proxy -> IX login
console.log("logged in as:", user.name, `(id ${user.id})`);
console.log("member of groups:", user.groupList);
