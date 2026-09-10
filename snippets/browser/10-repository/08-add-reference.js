// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    File an object into a second folder (reference, write)
// category: Repository & objects
// id:       repository.add-reference

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const makeFolder = async (name) => {
  const tpl = (await elo.call("createSord", {
    parentId: "1", maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  tpl.name = name;
  return String(await elo.call("checkinSord", {
    sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
  }));
};

let objId = null;
let target = null;
try {
  target = await makeFolder("pg-ref-target");
  objId = await makeFolder("pg-ref-object");
  try {
    await elo.call("refSord", { objId, oldParentId: "1", newParentId: target });
    console.log("reference added");
  } catch (exc) {
    console.log("refSord not permitted here:", exc.message);
  }
} finally {
  for (const oid of [objId, target]) {
    if (!oid) continue;
    try {
      await elo.call("deleteSord", { objId: oid, parentId: "1", deleteOptions: { deleteFinally: false } });
      await elo.call("deleteSord", { objId: oid, parentId: "1", deleteOptions: { deleteFinally: true } });
    } catch (e) { /* best effort */ }
  }
}
