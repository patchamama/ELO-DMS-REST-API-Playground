// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    CRUD Operations: create, read, update, delete an object
// category: Testing lab
// id:       lab.crud

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";
const PARENT = 1;

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

const got = (await elo.call("checkoutSord", {
  objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
console.log("read:", got.name, "|", got.desc);

got.name = "pg-lab-crud (renamed)";
await elo.call("checkinSord", { sord: got, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });
console.log("updated");

await elo.call("deleteSord", { parentId: String(PARENT), objId,
  deleteOptions: { deleteFinally: false } });
await elo.call("deleteSord", { parentId: String(PARENT), objId,
  deleteOptions: { deleteFinally: true } });
console.log("deleted:", objId);
