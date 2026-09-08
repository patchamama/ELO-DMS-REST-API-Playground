// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Start a workflow on an object (write)
// category: Workflows (advanced)
// id:       workflows.start

const elo = await connect();

const tmpls = (await elo.call("findFirstWorkflows", {
  findInfo: { type: { bset: "2" }, inclHidden: true },
  max: 5, wfDiagramZ: { bset: "0" },
})).workflows;
const tmpl = tmpls[0];
console.log(`using template ${tmpl.id} (${tmpl.name})`);

const flowId = await elo.call("startWorkFlow", {
  templFlowId: tmpl.id,
  flowName: "playground test workflow",
  objId: "1",
});
console.log("started workflow id:", flowId);
const res = await elo.call("checkoutWorkFlow", {
  flowId,
  typeZ: { bset: "0" },
  lockZ: { bset: "0" },
  workFlowDiagramZ: { bset: "1073741823" },
});
const wf = res.workflow || res;
console.log("workflow:", wf.name, (wf.nodes || []).map((n) => n.nodeName || n.name).filter(Boolean).slice(0, 8));
