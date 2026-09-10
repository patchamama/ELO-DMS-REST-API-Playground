// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Page through a large result set by hand
// category: Search
// id:       search.pagination

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

let res = await elo.call("findFirstSords", {
  findInfo: { findByIndex: { name: "Invoice *" } },
  max: 2,
  sordZ: { bset: "449304431574384639" },
});
const searchId = res.searchId;
let rows = [...(res.sords || [])];
console.log(`page 1: ${rows.length} rows`);
const sordZ = { bset: "449304431574384639" };
let page = 1;
while (res.moreResults && page++ < 3) {
  res = await elo.call("findNextSords", { searchId, idx: rows.length, max: 2, sordZ });
  rows = rows.concat(res.sords || []);
  console.log(`+ ${(res.sords || []).length} rows`);
}
await elo.call("findClose", { searchId });
console.log(`-> ${rows.length} rows so far (more available: ${!!res.moreResults})`);
