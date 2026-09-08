// import the shared client:  import { connect } from "elo-playground";
// topic:    Read a keyword list
// category: Keyword lists
// id:       keywords.list

import { connect } from "elo-playground";

const elo = await connect();

const res = await elo.call("checkoutKeywordList", {
  kwid: "ELOSTDSWL",
  max: 500,
  keywordZ: { bset: "7" },
});

const walk = (nodes, depth = 0) => {
  for (const n of nodes || []) {
    console.log("  ".repeat(depth + 1) + "- " + (n.text || "(no text)"));
    walk(n.children, depth + 1);
  }
};

const top = res.children || [];
console.log(`${res.id}: ${top.length} top-level entries`);
walk(top.slice(0, 8));
