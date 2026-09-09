// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    CRUD Operations: create, read, update, delete an object
// category: Testing lab
// id:       lab.crud

const elo = await connect();
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
