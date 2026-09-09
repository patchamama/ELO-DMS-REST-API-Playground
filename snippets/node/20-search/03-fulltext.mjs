// import the shared client:  import { connect } from "elo-playground";
// topic:    Full-text search
// category: Search
// id:       search.fulltext

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByFulltext: { fulltext: "agreement", isTree: false } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});

console.log(`${rows.length} documents match 'agreement'`);
rows.forEach((s) => console.log(`  ${s.name}`));
if (!rows.length) {
  console.log("  (0 hits usually means the ELO full-text service is not running " +
    "or has not finished indexing on this instance)");
}
