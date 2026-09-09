// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Rename an object (write)
// category: Repository & objects
// id:       repository.rename

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const tpl = (await elo.call("createSord", {
  parentId: "1", maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
tpl.name = "playground old name";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));

try {
  const sord = (await elo.call("checkoutSord", {
    objId, editInfoZ: { bset: "1", sordZ: { bset: ALL }, lockZ: { bset: "1" } },
  })).sord;
  console.log("before:", sord.name);
  sord.name = "playground new name";
  await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });
  console.log("renamed");
} catch (exc) {
  console.log("rename failed:", exc.message);
} finally {
  try {
    await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: false } });
    await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: true } });
  } catch (e) { /* best effort */ }
}
