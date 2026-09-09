// import the shared client:  import { connect } from "elo-playground";
// topic:    Start a workflow on an object (write)
// category: Workflows (advanced)
// id:       workflows.start

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ user: ELO_USER, password: ELO_PASS });
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
  // 1) pick a real template (ids are not guaranteed to start at 1)
  const tmpls = (await elo.call("findFirstWorkflows", {
    findInfo: { type: { bset: "2" }, inclHidden: true },
    max: 5, wfDiagramZ: { bset: "0" },
  })).workflows || [];
  if (!tmpls.length) {
    console.log("no workflow templates on this repository - nothing to start");
  } else {
    const tmpl = tmpls[0];
    console.log(`using template ${tmpl.id} (${tmpl.name})`);

    try {
      flowId = await elo.call("startWorkFlow", {
        templFlowId: tmpl.id, flowName: "playground test workflow", objId,
      });
      console.log("started workflow id:", flowId);

      const res = await elo.call("checkoutWorkFlow", {
        flowId,
        typeZ: { bset: "0" }, lockZ: { bset: "0" },
        workFlowDiagramZ: { bset: "1073741823" },
      });
      const wf = res.workflow || res;
      const nodes = (wf.nodes || []).map((n) => n.nodeName || n.name).filter(Boolean);
      console.log("workflow:", wf.name, " nodes:", nodes.slice(0, 8));
    } catch (exc) {
      if (exc instanceof EloError) console.log("could not start the workflow:", exc.message);
      else throw exc;
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
  elo.close();
}
