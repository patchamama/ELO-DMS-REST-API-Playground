// import the shared client:  import { connect } from "elo-playground";
// topic:    Copy a GRP (index) field value into a MAP field
// category: Testing lab
// id:       lab.grp-to-map

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";
const PARENT = 1;

let objId = null;
try {
  const tpl = (await elo.call("createSord", {
    parentId: String(PARENT), maskId: 0,
    editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  tpl.name = "pg-grp2map";
  objId = String(await elo.call("checkinSord", {
    sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
  }));
  console.log("scratch object:", objId);

  const sord = (await elo.call("checkoutSord", {
    objId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  const grp = {};
  for (const k of sord.objKeys || []) if (k.name) grp[k.name] = (k.data || [])[0];
  const sourceValue = grp.INVOICE_NO || grp.ELO_FN || "INV-2026-0042";
  console.log("GRP source value:", sourceValue);

  await elo.call("checkinMap", {
    objId: Number(objId), domainName: "objekte",
    data: [{ key: "grp_copy", value: sourceValue }],
    unlockZ: { bset: "1" }, // bset "1" commits; "0" does not
  });
  console.log(`wrote MAP grp_copy = ${sourceValue}`);

  const got = await elo.call("checkoutMap", {
    objId: Number(objId), id: objId, domainName: "objekte",
    keyNames: ["*"], lockZ: { bset: "0" },
  });
  console.log("MAP read-back:", got.items);
} catch (exc) {
  if (exc instanceof EloError) console.log("map operation failed:", exc.message);
  else throw exc;
} finally {
  if (objId) {
    try {
      await elo.call("deleteSord", { parentId: String(PARENT), objId, deleteOptions: { deleteFinally: false } });
      await elo.call("deleteSord", { parentId: String(PARENT), objId, deleteOptions: { deleteFinally: true } });
    } catch (exc) {
      console.log("cleanup failed:", exc.message);
    }
  }
  console.log("cleaned up");
  elo.close();
}
