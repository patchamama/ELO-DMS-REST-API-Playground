// import the shared client:  import { connect } from "elo-playground";
// topic:    List workflow templates and their diagram
// category: Workflows
// id:       workflows.templates

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

const res = await elo.call("findFirstWorkflows", {
  findInfo: { type: { bset: "2" }, inclHidden: true },   // 2 = TEMPLATE
  max: 100,
  wfDiagramZ: { bset: "1073741823" },                    // all diagram bits
});
const workflows = (res.workflows || []).sort((a, b) => (a.id || 0) - (b.id || 0));
console.log(`${workflows.length} templates. First few:`);

for (const wf of workflows.slice(0, 5)) {
  const nodes = (wf.nodes || []).map((n) => n.nodeName || n.name);
  const assocs = (wf.matrix || {}).assocs || [];
  console.log(`  [${wf.id}] ${wf.name}  -  ${nodes.length} nodes, ${assocs.length} connections`);
  nodes.slice(0, 6).forEach((n) => console.log(`        - ${n}`));
}
