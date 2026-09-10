// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Find a Business Solution config document
// category: Business Solutions
// id:       business-solutions.find-config

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const hits = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { name: "*.config.json" } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});
const doc = hits.find((s) => Number(s.type || 0) >= 254);
console.log("config document:", doc.name, "id", doc.id);
const info = await elo.call("checkoutDoc", {
  objId: String(doc.id),
  editInfoZ: { bset: "320", sordZ: { bset: "0" } },
});
// The bytes live on ELO's document connector - fetch them from the Python
// or Node snippet (the browser cannot reach it, CORS).
console.log("download url:", (info.document?.docs || [{}])[0].url);
