// import the shared client:  import { connect } from "elo-playground";
// topic:    CRUD Operations: create, read, update, delete an object
// category: Testing lab
// id:       lab.crud

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const PARENT = 1; // the folder to file the object under (its "path")

// --- CREATE ---------------------------------------------------
const tpl = (await elo.call("createSord", {
  parentId: String(PARENT), maskId: 0,
  editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
tpl.name = "pg-lab-crud";
tpl.desc = "created by the playground";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));
console.log("created:", objId);

// --- READ ---------------------------------------------------
const got = (await elo.call("checkoutSord", {
  objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log("read   :", got.name, "|", got.desc);

// --- UPDATE (read / modify / write) -----------------------
got.name = "pg-lab-crud (renamed)";
await elo.call("checkinSord", { sord: got, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });
const again = (await elo.call("checkoutSord", {
  objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log("updated:", again.name);

// --- DELETE (recycle bin, then purge) -------------------
await elo.call("deleteSord", { parentId: String(PARENT), objId,
  deleteOptions: { deleteFinally: false } });
await elo.call("deleteSord", { parentId: String(PARENT), objId,
  deleteOptions: { deleteFinally: true } });
console.log("deleted:", objId);
