// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Change owner, colour and permissions
// category: Testing lab
// id:       lab.owner-color-acl

const elo = await connect();
const ALL = "449304431574384639";

const tpl = (await elo.call("createSord", {
  parentId: "1", maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
tpl.name = "pg-owner-color-acl";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));

try {
  const palette = await elo.call("checkoutColors", { checkoutInfo: {} });
  console.log("palette:", palette.slice(0, 4).map((c) => [c.id, c.name]));

  const sord = (await elo.call("checkoutSord", {
    objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  sord.kind = 2;
  (sord.aclItems ||= []).push({ id: 9998, type: 0, access: 1 + 16 });
  await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });

  const after = (await elo.call("checkoutSord", {
    objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  console.log("colour id:", after.kind, "owner:", after.ownerName);
  console.log("acl:", (after.aclItems || []).map((a) => [a.name, a.access]));
} catch (exc) {
  console.log("operation failed:", exc.message);
} finally {
  try {
    await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: false } });
    await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: true } });
  } catch (e) { /* best effort */ }
}
