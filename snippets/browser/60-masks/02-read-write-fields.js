// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Read and write a Sord's index fields (write)
// category: Metadata masks
// id:       masks.read-write-fields

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const sord = (await elo.call("createSord", {
  parentId: 1, maskId: 34, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
sord.name = "playground fields demo";
for (const key of sord.objKeys) if (key.name === "BS_CONFIG_NAME") key.data = ["playground-value"];

const newId = String(await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } }));
try {
  const check = (await elo.call("checkoutSord", {
    objId: newId, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  console.log((check.objKeys || []).filter((k) => k.data && k.data.length).map((k) => `${k.name}=${k.data}`));
} catch (exc) {
  console.log("read/write failed:", exc.message);
} finally {
  for (const step of [false, true]) {
    try {
      await elo.call("deleteSord", { objId: newId, parentId: "1", deleteOptions: { deleteFinally: step } });
    } catch (e) { /* best effort */ }
  }
}
