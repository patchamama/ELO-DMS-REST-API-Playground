// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Find a Business Solution config document
// category: Business Solutions
// id:       business-solutions.find-config

const elo = await connect();

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
