// import the shared client:  import { connect } from "elo-playground";
// topic:    Search by an index-field value
// category: Search
// id:       search.by-field-value

import { connect } from "elo-playground";

const elo = await connect();

const field = "ELO_FNAME";  // a metadata field key
const value = "*.js";       // wildcards allowed

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { objKeys: [{ name: field, data: [value] }] } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});

console.log(`${rows.length} objects where ${field} matches ${JSON.stringify(value)}`);
rows.slice(0, 10).forEach((s) => console.log(`  - ${s.name}`));
