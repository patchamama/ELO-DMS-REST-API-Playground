// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Start a workflow on an object (write)
// category: Workflows (advanced)
// id:       workflows.start

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const tpl = (await elo.call("createSord", {
  parentId: "1", maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
tpl.name = "pg-workflow-target";
const objId = String(await elo.call("checkinSord", {
  sord: tpl, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
}));

let flowId = null;
try {
  const tmpls = (await elo.call("findFirstWorkflows", {
    findInfo: { type: { bset: "2" }, inclHidden: true },
    max: 5, wfDiagramZ: { bset: "0" },
  })).workflows || [];
  if (!tmpls.length) {
    console.log("no workflow templates on this repository - nothing to start");
  } else {
    try {
      flowId = await elo.call("startWorkFlow", {
        templFlowId: tmpls[0].id, flowName: "playground test workflow", objId,
      });
      console.log("started workflow id:", flowId);
    } catch (exc) {
      console.log("could not start the workflow:", exc.message);
    }
  }
} finally {
  if (flowId !== null) {
    for (const m of ["terminateWorkFlow", "deleteWorkFlow"]) {
      try { await elo.call(m, { flowId }); } catch (e) { /* best effort */ }
    }
  }
  for (const step of [false, true]) {
    try {
      await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: step } });
    } catch (e) { /* best effort */ }
  }
}
