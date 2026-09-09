// import the shared client:  import { connect } from "elo-playground";
// topic:    Read and write a Sord's index fields (write)
// category: Metadata masks
// id:       masks.read-write-fields

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const fields = (s) =>
  Object.fromEntries((s.objKeys || []).filter((k) => k.data && k.data.length).map((k) => [k.name, k.data]));

const sord = (await elo.call("createSord", {
  parentId: 1, maskId: 34, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
sord.name = "playground fields demo";

const wanted = { BS_CONFIG_NAME: ["playground-value"], BS_CONFIG_VERSION: ["1.0"] };
for (const key of sord.objKeys) if (wanted[key.name]) key.data = wanted[key.name];
console.log("before:", fields(sord));

const newId = String(await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } }));
try {
  const check = (await elo.call("checkoutSord", {
    objId: newId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  console.log("after: ", fields(check));
} catch (exc) {
  if (exc instanceof EloError) console.log("read/write failed:", exc.message);
  else throw exc;
} finally {
  for (const step of [false, true]) {
    try {
      await elo.call("deleteSord", { objId: newId, parentId: "1", deleteOptions: { deleteFinally: step } });
    } catch (e) { /* best effort */ }
  }
  elo.close();
}
