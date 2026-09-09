// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Resolve a GUID to an object (Sord)
// category: Repository & objects
// id:       repository.checkout-sord

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const objId = 2; // an int id or a "(GUID)" from the ELO client

const res = await elo.call("checkoutSord", {
  objId,
  editInfoZ: { bset: "1", sordZ: { bset: "449304431574384639" } },
});
const sord = res.sord;
const t = Number(sord.type || 0);
console.log((t >= 254 && t < 999 ? "document: " : "folder: ") + sord.name + " (id " + sord.id + ")");
