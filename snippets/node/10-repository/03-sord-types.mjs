// import the shared client:  import { connect } from "elo-playground";
// topic:    List Sord types (the entry icons)
// category: Repository & objects
// id:       repository.sord-types

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const res = await elo.call("checkoutSordTypes", { id: -1, sordTypeZ: { bset: "31" } });
const types = Array.isArray(res) ? res : res.sordTypes || [];

console.log(`${types.length} Sord types`);
for (const t of types) {
  console.log(`  [${String(t.id).padStart(4)}] ${t.name}  (${t.icon ? "icon" : "no icon"})`);
}
