// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Create a folder (write)
// category: Repository & objects
// id:       repository.create-folder

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const tmpl = await elo.call("createSord", {
  parentId: 1, maskId: 1,
  editInfoZ: { bset: "1", sordZ: { bset: ALL } },
});
const sord = tmpl.sord;
sord.name = "Playground test folder";
const newId = String(await elo.call("checkinSord", { sord, sordZ: { bset: ALL }, unlockZ: { bset: "1" } }));
console.log("created folder id:", newId);

try {
  for (const step of [false, true]) {
    await elo.call("deleteSord", { objId: newId, parentId: "1", deleteOptions: { deleteFinally: step } });
  }
  console.log("removed the test folder again");
} catch (exc) {
  console.log("could not remove the test folder:", exc.message);
}
