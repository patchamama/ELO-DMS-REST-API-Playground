// import the shared client:  import { connect } from "elo-playground";
// topic:    List session options
// category: Connection & session
// id:       connection.session-options

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const res = await elo.call("getSessionOptions", {});
const options = res.options || (Array.isArray(res) ? res : []);

console.log(`${options.length} session options`);
for (const opt of options.slice(0, 10)) {
  console.log(`  ${opt.key} = ${opt.value}`);
}
