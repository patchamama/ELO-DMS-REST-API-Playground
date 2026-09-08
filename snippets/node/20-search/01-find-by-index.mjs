// import the shared client:  import { connect } from "elo-playground";
// topic:    Find objects by index field
// category: Search
// id:       search.find-by-index

import { connect } from "elo-playground";

const elo = await connect();

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { name: "Invoice *", exactName: false } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});

console.log(`${rows.length} matches`);
for (const s of rows) console.log(`  ${s.name}  (mask: ${s.maskName})`);
