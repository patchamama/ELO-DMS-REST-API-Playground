// import the shared client:  import { connect } from "elo-playground";
// topic:    Search by an index-field value
// category: Search
// id:       search.by-field-value

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const field = "ELO_FNAME";  // a metadata field key
const value = "*.js";       // wildcards allowed

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { objKeys: [{ name: field, data: [value] }] } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});

console.log(`${rows.length} objects where ${field} matches ${JSON.stringify(value)}`);
rows.slice(0, 10).forEach((s) => console.log(`  - ${s.name}`));
