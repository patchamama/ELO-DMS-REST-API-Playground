// import the shared client:  import { connect } from "elo-playground";
// topic:    Check user/folder permissions
// category: Testing lab
// id:       lab.user-folder-permissions

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639"; // SordC.mbAllIndex - every Sord field, incl. aclItems

// access bits (AccessC.LUR_*): 1 R  2 W  4 D  8 E  16 L  32 P ; 63 = full
const ACCESS_BITS = [[1, "R"], [2, "W"], [4, "D"], [8, "E"], [16, "L"], [32, "P"]];

function accessLabel(bits) {
  if (bits === 63) return "full";
  if (!bits) return "no access";
  return ACCESS_BITS.filter(([bit]) => bits & bit).map(([, name]) => name).join(", ");
}

function resolveAccess(aclItems, principalIds) {
  // A principal - their own id, plus (for a user) every group id they
  // belong to - has access when any of those ids appears in aclItems.
  let bits = 0;
  for (const entry of aclItems) {
    if (principalIds.has(Number(entry.id))) bits |= Number(entry.access || 0);
  }
  return bits;
}

async function folderChildren(parentId) {
  // One level of the ELO folder tree, folders only (mirrors the Testing
  // lab filesystem panel's list_children).
  const res = await elo.call("findFirstSords", {
    findInfo: { findChildren: { parentId: String(parentId), mainParent: true, endLevel: 1 } },
    max: 1000,
    sordZ: { bset: ALL },
  });
  const rows = (res.sords || []).filter((s) => Number(s.type || 0) < 254);
  if (res.searchId) await elo.call("findClose", { searchId: res.searchId });
  return rows;
}

async function folderAcl(folderId) {
  const res = await elo.call("checkoutSord", {
    objId: String(folderId), editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  });
  return res.sord.aclItems || [];
}

// groups and users - the same findFirstUsers/findNextUsers loop as
// catalog "List users (and groups)"; onlyGroups vs onlyUsers selects which.
const groups = await elo.findAll("findFirstUsers", "findNextUsers", "sortedResult", { findUserInfo: { onlyGroups: true }, max: 200 });
const users = await elo.findAll("findFirstUsers", "findNextUsers", "sortedResult", { findUserInfo: { onlyUsers: true }, max: 200 });
console.log(`${groups.length} groups, ${users.length} users`);

// One batched checkoutUsers call resolves every user's groupList at once.
let detail = await elo.call("checkoutUsers", {
  ids: users.map((u) => u.id),
  checkoutUsersZ: { bset: "513" }, // CHECKOUT_USERS.BY_IDS
});
detail = Array.isArray(detail) ? detail : detail.result || detail.users || [];
const groupLists = new Map(detail.map((u) => [Number(u.id), u.groupList || []]));

// Pick the first group as the demo principal - the interactive panel lets
// you click any group or user in the left-hand list instead.
const principal = groups[0];
const principalIds = new Set([Number(principal.id)]);
const members = users.filter((u) => (groupLists.get(Number(u.id)) || []).includes(Number(principal.id)));
console.log(`\n${principal.name} members (${members.length}):`, members.slice(0, 10).map((u) => u.name));

// Walk the folder tree from the repository root, printing each folder's
// permission label for the chosen principal - exactly what the interactive
// panel's right-hand tree renders (greyed out + struck through at "no access").
async function walk(parentId, indent = 0) {
  for (const row of await folderChildren(parentId)) {
    const bits = resolveAccess(await folderAcl(row.id), principalIds);
    console.log("  ".repeat(indent) + `${row.name} (${accessLabel(bits)})`);
    if (Number(row.childCount || 0)) await walk(row.id, indent + 1);
  }
}

console.log(`\nfolders visible to ${principal.name}:`);
try {
  await walk("1");
} catch (exc) {
  if (exc instanceof EloError) console.log("could not read the tree:", exc.message);
  else throw exc;
}
elo.close();
