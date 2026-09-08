// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Resolve a GUID to an object (Sord)
// category: Repository & objects
// id:       repository.checkout-sord

const elo = await connect();
const objId = 2; // an int id or a "(GUID)" from the ELO client

const res = await elo.call("checkoutSord", {
  objId,
  editInfoZ: { bset: "1", sordZ: { bset: "449304431574384639" } },
});
const sord = res.sord;
const t = Number(sord.type || 0);
console.log((t >= 254 && t < 999 ? "document: " : "folder: ") + sord.name + " (id " + sord.id + ")");
