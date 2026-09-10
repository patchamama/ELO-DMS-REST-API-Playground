// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Read a keyword list
// category: Keyword lists
// id:       keywords.list

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const res = await elo.call("checkoutKeywordList", { kwid: "ELOSTDSWL", max: 500, keywordZ: { bset: "7" } });
const top = res.children || [];
console.log(`${res.id}: ${top.length} top-level entries`);
top.slice(0, 8).forEach((n) => console.log("  - " + (n.text || "(no text)")));
