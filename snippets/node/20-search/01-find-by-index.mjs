// import the shared client:  import { connect } from "elo-playground";
// topic:    Find objects by index field
// category: Search
// id:       search.find-by-index

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { name: "Invoice *", exactName: false } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});

console.log(`${rows.length} matches`);
for (const s of rows) console.log(`  ${s.name}  (mask: ${s.maskName})`);
