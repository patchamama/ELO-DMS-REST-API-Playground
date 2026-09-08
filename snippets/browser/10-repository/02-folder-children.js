// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List the children of a folder
// category: Repository & objects
// id:       repository.folder-children

const elo = await connect();

const rows = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findChildren: { parentId: 1, mainParent: true, endLevel: 2 } },
  max: 100,
  sordZ: { bset: "449304431574384639" },
});
console.log(`${rows.length} objects under the root`);
rows.forEach((s) => console.log(`  [${s.id}] ${s.name} (${s.childCount || 0} children)`));
