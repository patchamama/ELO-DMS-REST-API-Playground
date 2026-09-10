// import the shared client:  import { connect } from "elo-playground";
// topic:    Find an object by GUID, id or name
// category: Testing lab
// id:       lab.find

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

// --- by integer id ---------------------------------------------
const byId = (await elo.call("checkoutSord", {
  objId: 2,                                    // "Administration" on any repo
  editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log(`by id 2   -> ${byId.name}  guid ${byId.guid}`);

// --- by GUID (objId also accepts a "(GUID)") -----------------
const byGuid = (await elo.call("checkoutSord", {
  objId: byId.guid,
  editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log(`by guid   -> ${byGuid.name}  (id ${byGuid.id})`);

// --- by name (findByIndex.name, '*' wildcards) --------------
const res = await elo.call("findFirstSords", {
  findInfo: { findByIndex: { name: "Administration*" } },
  max: 10,
  sordZ: { bset: ALL },
});
console.log("by name   ->", (res.sords || []).map((s) => [s.id, s.name]));
await elo.call("findClose", { searchId: res.searchId });

// For CONTENT search use findByFulltext (iSearch / Elasticsearch).
