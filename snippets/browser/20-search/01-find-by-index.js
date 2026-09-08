// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Find objects by index field
// category: Search
// id:       search.find-by-index

const elo = await connect();

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { name: "Invoice *", exactName: false } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});
console.log(`${rows.length} matches`);
rows.forEach((s) => console.log(`  ${s.name} (mask: ${s.maskName})`));
