// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Full-text search
// category: Search
// id:       search.fulltext

const elo = await connect();

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByFulltext: { fulltext: "agreement", isTree: false } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});
console.log(`${rows.length} documents match 'agreement'`);
rows.forEach((s) => console.log(`  ${s.name}`));
