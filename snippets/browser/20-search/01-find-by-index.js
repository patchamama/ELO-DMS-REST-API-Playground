// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Find objects by index field
// category: Search
// id:       search.find-by-index

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { name: "Invoice *", exactName: false } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});
console.log(`${rows.length} matches`);
rows.forEach((s) => console.log(`  ${s.name} (mask: ${s.maskName})`));
