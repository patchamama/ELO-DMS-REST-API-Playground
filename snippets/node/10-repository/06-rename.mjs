// import the shared client:  import { connect } from "elo-playground";
// topic:    Rename an object (write)
// category: Repository & objects
// id:       repository.rename

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

// Provision a throwaway folder so this snippet is self-contained.
const tpl = (await elo.call("createSord", {
  parentId: "1", maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
tpl.name = "playground old name";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));

try {
  // 1) check it out (with a lock)
  const sord = (await elo.call("checkoutSord", {
    objId,
    editInfoZ: { bset: "1", sordZ: { bset: ALL }, lockZ: { bset: "1" } },
  })).sord;
  console.log("before:", sord.name);

  // 2) change the name, 3) check it back in and release the lock
  sord.name = "playground new name";
  await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } });

  const after = (await elo.call("checkoutSord", {
    objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  console.log("after: ", after.name);
} catch (exc) {
  if (exc instanceof EloError) console.log("rename failed:", exc.message);
  else throw exc;
} finally {
  try {
    await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: false } });
    await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: true } });
  } catch (e) { /* best effort */ }
  elo.close();
}
