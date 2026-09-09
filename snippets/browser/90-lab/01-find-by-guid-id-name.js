// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Find an object by GUID, id or name
// category: Testing lab
// id:       lab.find

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const byId = (await elo.call("checkoutSord", {
  objId: 2, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log("by id 2 ->", byId.name, byId.guid);

const byGuid = (await elo.call("checkoutSord", {
  objId: byId.guid, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log("by guid ->", byGuid.name, "(id " + byGuid.id + ")");

const res = await elo.call("findFirstSords", {
  findInfo: { findByIndex: { name: "Administration*" } },
  max: 10, sordZ: { bset: ALL },
});
console.log("by name ->", (res.sords || []).map((s) => [s.id, s.name]));
await elo.call("findClose", { searchId: res.searchId });
