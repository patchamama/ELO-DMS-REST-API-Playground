// import the shared client:  import { connect } from "elo-playground";
// topic:    Delete an object (write, two steps)
// category: Repository & objects
// id:       repository.delete-sord

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
tpl.name = "pg-delete-me";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));
console.log("scratch folder:", objId);

try {
  // step 1 - move it to the recycle bin
  await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: false } });
  console.log("step 1 (to recycle bin): ok");

  // step 2 - purge it for good
  await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: true } });
  console.log("step 2 (purge):          ok");

  // confirm it is gone
  try {
    await elo.call("checkoutSord", { objId, editInfoZ: { bset: "1", sordZ: { bset: "0" } } });
    console.log("gone: false");
  } catch (e) {
    if (e instanceof EloError) console.log("gone: true");
    else throw e;
  }
} finally {
  elo.close();
}
