// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Delete an object (write, two steps)
// category: Repository & objects
// id:       repository.delete-sord

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const tpl = (await elo.call("createSord", {
  parentId: "1", maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
tpl.name = "pg-delete-me";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));
console.log("scratch folder:", objId);

await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: false } });
console.log("step 1 (to recycle bin): ok");
await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: true } });
console.log("step 2 (purge): ok");
