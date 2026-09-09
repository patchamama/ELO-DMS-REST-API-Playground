// import the shared client:  import { connect } from "elo-playground";
// topic:    Change owner, colour and permissions
// category: Testing lab
// id:       lab.owner-color-acl

import { connect } from "elo-playground";

const elo = await connect();
const ALL = "449304431574384639";

const objId = "5500"; // a throwaway object

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
