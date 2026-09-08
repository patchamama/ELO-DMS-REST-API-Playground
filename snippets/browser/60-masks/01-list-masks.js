// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List metadata masks and their fields
// category: Metadata masks
// id:       masks.list

const elo = await connect();
const KINDS = { 3000: "text", 3004: "iso-date", 3002: "number", 3005: "keyword-list" };
const masks = await elo.findAll(
  "findFirstDocMasks", "findNextDocMasks", "docMasks",
  { findInfo: { packageGuid: "", maskIdsOrNames: [] }, max: 500 },
);
masks.forEach((m) => {
  const fields = (m.lines || []).map((ln) => `${ln.name} [${KINDS[ln.type] || ln.type}]`);
  console.log(`${m.name}: ${fields.join(", ")}`);
});
