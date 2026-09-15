// import the shared client:  import { connect } from "elo-playground";
// topic:    Most used workflows
// category: Testing lab
// id:       lab.workflow-usage

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

// WFTypeC: 1 = active, 2 = template, 4 = finished (a WFTypeZ bitset, not an int).
// WFDiagramC bits: 0 id/name/version, 4 completionDateIso, 5 nodes,
// 9 startDateIso, 11 ownerName, 15 templateName, 23 objName.
const TEMPLATE_Z = String((1 << 0) | (1 << 5) | (1 << 11));
const INSTANCE_Z = String((1 << 0) | (1 << 4) | (1 << 9) | (1 << 11) | (1 << 15) | (1 << 23));

async function findWorkflows(wfType, bset) {
  // findFirstWorkflows / findNextWorkflows / findClose - rows in "workflows"
  let res = await elo.call("findFirstWorkflows", { findInfo: { type: { bset: wfType } }, max: 500, wfDiagramZ: { bset } });
  const rows = [...(res.workflows || [])];
  while (res.moreResults) {
    res = await elo.call("findNextWorkflows", { searchId: res.searchId, idx: rows.length, max: 500, wfDiagramZ: { bset } });
    if (!(res.workflows || []).length) break;
    rows.push(...res.workflows);
  }
  if (res.searchId) await elo.call("findClose", { searchId: res.searchId });
  return rows;
}

const templates = await findWorkflows("2", TEMPLATE_Z);
const active = await findWorkflows("1", INSTANCE_Z);
const finished = await findWorkflows("4", INSTANCE_Z); // only what cleanup has not removed yet
console.log(`${templates.length} templates, ${active.length} active, ${finished.length} finished workflows on the server\n`);

// ELO keeps no usage counter: count the instances per templateId ourselves.
const stats = new Map();
const bucket = (tid) => stats.get(tid) || stats.set(tid, { started: 0, active: 0, finished: 0, last: "", lastObj: "" }).get(tid);
for (const [kind, rows] of [["active", active], ["finished", finished]]) {
  for (const w of rows) {
    const s = bucket(String(w.templateId));
    s.started += 1;
    s[kind] += 1;
    if ((w.startDateIso || "") > s.last) { s.last = w.startDateIso; s.lastObj = w.objName || ""; }
  }
}
for (const t of templates) bucket(String(t.id)); // unused templates still show up, with 0

const names = new Map(templates.map((t) => [String(t.id), t.name]));
const ranked = [...stats.entries()].sort((a, b) => b[1].started - a[1].started || (names.get(a[0]) || a[0]).localeCompare(names.get(b[0]) || b[0]));
console.log(`  #  started  active  finished  last start        template                                  nodes`);
ranked.slice(0, 25).forEach(([tid, s], i) => {
  const tpl = templates.find((t) => String(t.id) === tid) || {};
  const d = s.last;
  const last = d ? `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)} ${d.slice(8, 10)}:${d.slice(10, 12)}` : "";
  // templates carry no description field; the start node's comment is the closest thing
  const desc = (((tpl.nodes || [])[0] || {}).comment || "").trim();
  console.log(` ${String(i + 1).padStart(2)}  ${String(s.started).padStart(7)}  ${String(s.active).padStart(6)}  ${String(s.finished).padStart(8)}  ${last.padEnd(16)}  ${(names.get(tid) || tid).slice(0, 40).padEnd(40)}  ${String((tpl.nodes || []).length).padStart(5)}` + (desc ? `   ${desc.slice(0, 40)}` : ""));
});
elo.close();
