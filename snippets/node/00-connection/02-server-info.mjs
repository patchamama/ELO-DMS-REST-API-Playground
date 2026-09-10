// import the shared client:  import { connect } from "elo-playground";
// topic:    Read server info and licence
// category: Connection & session
// id:       connection.server-info

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });  // env vars + login() already done

const info = await elo.call("getServerInfo", {});
const server = (info.indexServers || [{}])[0];
const lic = (info.license || {}).licenseOptions || {};

console.log("repository :", server.arcName);
console.log("IX version :", info.version);
console.log("database   :", info.databaseEngine);
console.log("product    :", lic.product, "/ users:", lic.usercount1);
