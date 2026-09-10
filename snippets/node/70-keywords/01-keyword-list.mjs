// import the shared client:  import { connect } from "elo-playground";
// topic:    Read a keyword list
// category: Keyword lists
// id:       keywords.list

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

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
