// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Read server info and licence
// category: Connection & session
// id:       connection.server-info

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const info = await elo.call("getServerInfo", {});
const server = (info.indexServers || [{}])[0];
console.log("repository :", server.arcName);
console.log("IX version :", info.version);
console.log("database   :", info.databaseEngine);
