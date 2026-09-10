// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Link two objects (and remove the link)
// category: Testing lab
// id:       lab.links

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";
const PARENT = 1;

const makeFolder = async (name) => {
  const tpl = (await elo.call("createSord", {
    parentId: String(PARENT), maskId: 0,
    editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  tpl.name = name;
  return String(await elo.call("checkinSord", {
    sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
  }));
};

let a = null;
let b = null;
try {
  a = await makeFolder("pg-link-A");
  b = await makeFolder("pg-link-B");
  console.log(`created A=${a}  B=${b}`);
  await elo.call("linkSords", { fromId: a, toIds: [b], linkZ: { bset: "1" } });
  const out = (await elo.call("checkoutSord", {
    objId: a, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
  })).sord;
  console.log("linked  -> A.linksGoOut =", (out.linksGoOut || []).map((l) => l.id));
  await elo.call("unlinkSords", { fromId: a, toIds: [b], linkZ: { bset: "1" } });
  console.log("unlinked");
} catch (exc) {
  console.log("link operation failed:", exc.message);
} finally {
  for (const oid of [a, b]) {
    if (!oid) continue;
    try {
      await elo.call("deleteSord", { parentId: String(PARENT), objId: oid, deleteOptions: { deleteFinally: false } });
      await elo.call("deleteSord", { parentId: String(PARENT), objId: oid, deleteOptions: { deleteFinally: true } });
    } catch (exc) { /* best effort */ }
  }
  console.log("cleaned up");
}
