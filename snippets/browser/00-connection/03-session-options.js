// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List session options
// category: Connection & session
// id:       connection.session-options

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const res = await elo.call("getSessionOptions", {});
const options = res.options || (Array.isArray(res) ? res : []);
console.log(`${options.length} session options`);
options.slice(0, 10).forEach((o) => console.log(`  ${o.key} = ${o.value}`));
