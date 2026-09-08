// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    List workflow templates and their diagram
// category: Workflows
// id:       workflows.templates

const elo = await connect();

const res = await elo.call("findFirstWorkflows", {
  findInfo: { type: { bset: "2" }, inclHidden: true },
  max: 100,
  wfDiagramZ: { bset: "1073741823" },
});
const workflows = (res.workflows || []).sort((a, b) => (a.id || 0) - (b.id || 0));
console.log(`${workflows.length} templates. First few:`);
workflows.slice(0, 5).forEach((wf) => {
  const nodes = (wf.nodes || []).map((n) => n.nodeName || n.name);
  console.log(`  [${wf.id}] ${wf.name}  -  ${nodes.length} nodes`);
});
