// import the shared client:  import { connect } from "elo-playground";
// topic:    Page through a large result set by hand
// category: Search
// id:       search.pagination

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const body = {
  findInfo: { findByIndex: { name: "Invoice *" } },
  max: 2,                                        // tiny page size to force paging
  sordZ: { bset: "449304431574384639" },
};
let res = await elo.call("findFirstSords", body);
const searchId = res.searchId;
let rows = [...(res.sords || [])];
console.log(`page 1: ${rows.length} rows, moreResults=${res.moreResults}`);

let page = 1;
while (res.moreResults && page < 3) {              // stop after a few pages for the demo
  page += 1;
  res = await elo.call("findNextSords", {
    searchId, idx: rows.length, max: 2,
    sordZ: body.sordZ,               // IX needs the selector on every page
  });
  rows = rows.concat(res.sords || []);
  console.log(`page ${page}: ${(res.sords || []).length} rows, moreResults=${res.moreResults}`);
}

await elo.call("findClose", { searchId });        // release the search
console.log(`-> ${rows.length} rows so far (more available: ${!!res.moreResults})`);
