// import the shared client:  import { connect } from "elo-playground";
// topic:    Change owner, colour and permissions
// category: Testing lab
// id:       lab.owner-color-acl

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

// Provision a throwaway folder so this snippet is self-contained.
const tpl = (await elo.call("createSord", {
  parentId: "1", maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
tpl.name = "pg-owner-color-acl";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));

try {
  // the colour palette (id -> name)
  const palette = await elo.call("checkoutColors", { checkoutInfo: {} });
  console.log("palette:", palette.slice(0, 4).map((c) => [c.id, c.name]));

  // read / modify / write
  const sord = (await elo.call("checkoutSord", {
    objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;

  sord.kind = 2; // 'kind' == colour id from the palette

  // owner: an int user id. Reassigning needs a main-admin; ownerName is read-only.
  // sord.ownerId = 123;

  // permissions: append an ACL entry { id, type, access }
  //   type 0 = user/group id ; access bits: 1 R  2 W  4 D  8 rights  16 L  32 P
  (sord.aclItems ||= []).push({ id: 9998, type: 0, access: 1 + 16 });

  await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });

  const after = (await elo.call("checkoutSord", {
    objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  console.log("colour id:", after.kind, "  owner:", after.ownerName);
  console.log("acl:", (after.aclItems || []).map((a) => [a.name, a.access]));
} catch (exc) {
  if (exc instanceof EloError) console.log("operation failed:", exc.message);
  else throw exc;
} finally {
  try {
    await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: false } });
    await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: true } });
  } catch (e) { /* best effort */ }
  elo.close();
}
