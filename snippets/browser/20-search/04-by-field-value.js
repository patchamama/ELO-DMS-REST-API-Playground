// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Search by an index-field value
// category: Search
// id:       search.by-field-value

const elo = await connect();

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { objKeys: [{ name: "ELO_FNAME", data: ["*.js"] }] } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});
console.log(`${rows.length} objects`);
rows.slice(0, 10).forEach((s) => console.log(`  - ${s.name}`));
