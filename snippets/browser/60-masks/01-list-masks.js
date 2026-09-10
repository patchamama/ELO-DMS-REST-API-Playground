// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List metadata masks and their fields
// category: Metadata masks
// id:       masks.list

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const KINDS = { 3000: "text", 3004: "iso-date", 3002: "number", 3005: "keyword-list" };
const masks = await elo.findAll(
  "findFirstDocMasks", "findNextDocMasks", "docMasks",
  { findInfo: { packageGuid: "", maskIdsOrNames: [] }, max: 500 },
);
masks.forEach((m) => {
  const fields = (m.lines || []).map((ln) => `${ln.name} [${KINDS[ln.type] || ln.type}]`);
  console.log(`${m.name}: ${fields.join(", ")}`);
});
