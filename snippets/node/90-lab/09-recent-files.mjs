// import the shared client:  import { connect } from "elo-playground";
// topic:    Browse folders and preview the newest files
// category: Testing lab
// id:       lab.recent-files

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

// Only the Sord members the listing needs - paging stays fast. SordC bits:
// 5 name, 7 IDateIso (modified), 17 ownerName, 54 docVersion, 59 refPaths.
const LEAN = String((1n << 5n) | (1n << 7n) | (1n << 17n) | (1n << 54n) | (1n << 59n));
const FOLDER_ID = "2"; // the folder to look below ("1" = repository root)
const DAYS_BACK = 30;

const compact = (d) => d.toISOString().replace(/[-:T]/g, "").slice(0, 14);
const since = compact(new Date(Date.now() - DAYS_BACK * 86400e3));
const until = compact(new Date(Date.now() + 86400e3));

// An indexed range search on the modification date - there is no cheap
// "recursive children, newest first" query in IX.
let res = await elo.call("findFirstSords", {
  findInfo: { findByIndex: { iDateIso: `${since}...${until}` }, findByType: { typeDocuments: true } },
  max: 500,
  sordZ: { bset: LEAN },
});
const rows = [...(res.sords || [])];
while (res.moreResults) {
  res = await elo.call("findNextSords", { searchId: res.searchId, idx: rows.length, max: 500, sordZ: { bset: LEAN } });
  if (!(res.sords || []).length) break;
  rows.push(...res.sords);
}
if (res.searchId) await elo.call("findClose", { searchId: res.searchId });

// refPaths[0].path = the folders from below the root down to the parent
const pathOf = (row) => (((row.refPaths || [])[0] || {}).path || []).map((p) => [String(p.id), p.name]);

const hits = rows
  .filter((r) => FOLDER_ID === "1" || pathOf(r).some(([id]) => id === FOLDER_ID) || String(r.parentId) === FOLDER_ID)
  .sort((a, b) => (b.IDateIso || "").localeCompare(a.IDateIso || ""));
console.log(`newest documents below folder ${FOLDER_ID} (last ${DAYS_BACK} days, ${hits.length} found):`);
for (const r of hits.slice(0, 50)) {
  const dv = r.docVersion || {};
  const d = r.IDateIso;
  console.log(`${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)} ${d.slice(8, 10)}:${d.slice(10, 12)}  ${(dv.ext || "").padEnd(5)} ${String(dv.size || 0).padStart(8)} B  ${r.name.slice(0, 40).padEnd(40)} ${pathOf(r).map(([, n]) => n).join(" / ")}`);
}

// preview the newest one: checkoutDoc hands out a download URL for this session
if (hits.length) {
  const doc = hits[0];
  const info = await elo.call("checkoutDoc", { objId: String(doc.id), editInfoZ: { bset: "320", sordZ: { bset: "0" } } });
  const first = ((info.document || {}).docs || [{}])[0];
  try {
    const text = await elo.download(first.url, { maxBytes: 200000 });
    console.log(`\n--- ${doc.name} (${first.ext}) ---\n` + String(text).split("\n").slice(0, 10).join("\n"));
  } catch (exc) {
    if (exc instanceof EloError) console.log("could not download:", exc.message);
    else throw exc;
  }
}
elo.close();
