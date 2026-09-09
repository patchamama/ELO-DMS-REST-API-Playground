// import the shared client:  import { connect } from "elo-playground";
// topic:    List the children of a folder
// category: Repository & objects
// id:       repository.folder-children

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });

// findAll() runs findFirstSords -> findNextSords -> findClose for us.
const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findChildren: { parentId: 1, mainParent: true, endLevel: 2 } },
  max: 100,
  sordZ: { bset: "449304431574384639" },
});

console.log(`${rows.length} objects under the root`);
for (const s of rows) {
  console.log(`  [${String(s.id).padStart(5)}] ${s.name}  (${s.childCount || 0} children)`);
}
