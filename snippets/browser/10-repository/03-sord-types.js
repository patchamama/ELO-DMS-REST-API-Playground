// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List Sord types (the entry icons)
// category: Repository & objects
// id:       repository.sord-types

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const res = await elo.call("checkoutSordTypes", { id: -1, sordTypeZ: { bset: "31" } });
const types = Array.isArray(res) ? res : res.sordTypes || [];
console.log(`${types.length} Sord types`);
types.forEach((t) => console.log(`  [${t.id}] ${t.name}`));
