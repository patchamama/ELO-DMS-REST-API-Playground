// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List the children of a folder
// category: Repository & objects
// id:       repository.folder-children

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findChildren: { parentId: 1, mainParent: true, endLevel: 2 } },
  max: 100,
  sordZ: { bset: "449304431574384639" },
});
console.log(`${rows.length} objects under the root`);
rows.forEach((s) => console.log(`  [${s.id}] ${s.name} (${s.childCount || 0} children)`));
