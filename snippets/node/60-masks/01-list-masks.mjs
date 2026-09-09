// import the shared client:  import { connect } from "elo-playground";
// topic:    List metadata masks and their fields
// category: Metadata masks
// id:       masks.list

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });

// DocMaskLine.type -> readable kind (ELO 25 DOC_MASK_LINE constants, abridged)
const KINDS = { 3000: "text", 3001: "date", 3002: "number", 3004: "iso-date",
                3005: "keyword-list", 3006: "user", 3013: "integer" };

const masks = await elo.findAll(
  "findFirstDocMasks", "findNextDocMasks", "docMasks",
  { findInfo: { packageGuid: "", maskIdsOrNames: [] }, max: 500 },
);

for (const m of masks) {
  const fields = (m.lines || []).map((ln) => `${ln.name} [${KINDS[ln.type] || ln.type}]`);
  console.log(`${m.name} (${fields.length} fields): ${fields.join(", ")}`);
}
