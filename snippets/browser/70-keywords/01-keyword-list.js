// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Read a keyword list
// category: Keyword lists
// id:       keywords.list

const elo = await connect();
const res = await elo.call("checkoutKeywordList", { kwid: "ELOSTDSWL", max: 500, keywordZ: { bset: "7" } });
const top = res.children || [];
console.log(`${res.id}: ${top.length} top-level entries`);
top.slice(0, 8).forEach((n) => console.log("  - " + (n.text || "(no text)")));
