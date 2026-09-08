// import the shared client:  import { connect } from "elo-playground";
// topic:    Start a workflow on an object (write)
// category: Workflows (advanced)
// id:       workflows.start

import { connect } from "elo-playground";

const elo = await connect();

// 1) pick a real template (ids are not guaranteed to start at 1)
const tmpls = (await elo.call("findFirstWorkflows", {
  findInfo: { type: { bset: "2" }, inclHidden: true },
  max: 5, wfDiagramZ: { bset: "0" },
})).workflows;
const tmpl = tmpls[0];
console.log(`using template ${tmpl.id} (${tmpl.name})`);

// 2) start it on an object - use a throwaway folder for objId
const objId = 1; // replace with a throwaway object's id

const flowId = await elo.call("startWorkFlow", {
  templFlowId: tmpl.id,
  flowName: "playground test workflow",
  objId: String(objId),
});
console.log("started workflow id:", flowId);

// 3) read the running instance back (there is no getWorkFlowStatus)
const res = await elo.call("checkoutWorkFlow", {
  flowId,
  typeZ: { bset: "0" },                  // 0 = running instance (2 = template)
  lockZ: { bset: "0" },                  // no lock
  workFlowDiagramZ: { bset: "1073741823" },
});
const wf = res.workflow || res;
const nodes = (wf.nodes || []).map((n) => n.nodeName || n.name).filter(Boolean);
console.log("workflow:", wf.name, " nodes:", nodes.slice(0, 8));
