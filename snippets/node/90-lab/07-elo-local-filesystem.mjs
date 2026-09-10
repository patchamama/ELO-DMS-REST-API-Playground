// import the shared client:  import { connect } from "elo-playground";
// topic:    Generate an ELO structure on the local filesystem (and back)
// category: Testing lab
// id:       lab.fs-sync

import { connect, EloError } from "elo-playground";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const FOLDER_ID = "1";                 // the ELO folder to mirror (1 = repository root)
const DEST = "elo-archiv-structure";   // local target; the panel above uses sandbox/<this>
const MAX_BYTES = 25 * 1024 * 1024;    // per-document cap (Node download() returns text)

// the picked folder itself becomes the top directory of the mirror
const picked = (await elo.call("checkoutSord", {
  objId: FOLDER_ID, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord || {};
const top = String(picked.name || "").replace(/[<>:"/\\|?*]/g, "_").trim() || `folder-${FOLDER_ID}`;
const DEST_ROOT = join(DEST, top);

const xmlEsc = (v) =>
  String(v == null ? "" : v).replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" }[c]));

async function writeMeta(objId, dir) {
  // metadata.opf: mask + GRP/MAP field values + dates, for a later re-import
  let sd = {};
  let mp = [];
  try {
    sd = (await elo.call("checkoutSord", {
      objId: String(objId), editInfoZ: { bset: "1", sordZ: { bset: ALL } },
    })).sord || {};
  } catch (exc) {
    if (exc instanceof EloError) { console.log("meta skip", objId, "-", exc.message); return; }
    throw exc;
  }
  try {
    mp = (await elo.call("checkoutMap", {
      objId: Number(objId), id: String(objId), domainName: "objekte",
      keyNames: ["*"], lockZ: { bset: "0" },
    })).items || [];
  } catch (e) { mp = []; }
  const grp = (sd.objKeys || [])
    .filter((k) => k.name)
    .map((k) => `    <field name="${xmlEsc(k.name)}">` +
      (k.data || []).map((v) => `<value>${xmlEsc(v)}</value>`).join("") + "</field>")
    .join("\n");
  const map = (mp || [])
    .map((it) => `    <field key="${xmlEsc(it.key)}"><value>${xmlEsc(it.value)}</value></field>`)
    .join("\n");
  const xml =
    '<?xml version="1.0" encoding="utf-8"?>\n' +
    '<eloContainer generator="elo-api-playground">\n' +
    `  <source objId="${xmlEsc(sd.id)}" guid="${xmlEsc(sd.guid)}" />\n` +
    "  <sord>\n" +
    `    <name>${xmlEsc(sd.name)}</name>\n` +
    `    <desc>${xmlEsc(sd.desc)}</desc>\n` +
    `    <mask id="${xmlEsc(sd.mask)}" name="${xmlEsc(sd.maskName)}" />\n` +
    `    <dates iDateIso="${xmlEsc(sd.IDateIso)}" xDateIso="${xmlEsc(sd.XDateIso)}" />\n` +
    "  </sord>\n" +
    `  <groupFields>\n${grp}\n  </groupFields>\n` +
    `  <mapFields>\n${map}\n  </mapFields>\n` +
    "</eloContainer>\n";
  await writeFile(join(dir, "metadata.opf"), xml);
}

async function children(parentId) {
  const res = await elo.call("findFirstSords", {
    findInfo: { findChildren: { parentId: String(parentId), mainParent: true, endLevel: 1 } },
    max: 1000, sordZ: { bset: ALL },
  });
  const rows = res && res.sords ? res.sords : [];
  if (res && res.searchId) {
    try { await elo.call("findClose", { searchId: res.searchId }); } catch (e) { /* ignore */ }
  }
  return rows;
}

let folders = 0;
let docs = 0;

async function mirror(parentId, dir) {
  await mkdir(dir, { recursive: true });
  await writeMeta(parentId, dir);                      // one metadata.opf per container
  for (const s of await children(parentId)) {
    const name = String(s.name || s.id).replace(/[/\\]/g, "_");
    if (Number(s.type || 0) < 254) {
      folders += 1;
      await mirror(s.id, join(dir, name));
    } else {
      try {
        const info = await elo.call("checkoutDoc", {
          objId: s.id, editInfoZ: { bset: "320", sordZ: { bset: "0" } },
        });
        const d = (((info.document || {}).docs) || [])[0];
        if (!d || !d.url) continue;
        const ext = String(d.ext || "").replace(/^\./, "");
        const body = await elo.download(d.url, { maxBytes: MAX_BYTES });
        const fname = name.includes(".") || !ext ? name : `${name}.${ext}`;
        await writeFile(join(dir, fname), body);
        docs += 1;
      } catch (exc) {
        if (exc instanceof EloError) console.log("skip", name, "-", exc.message);
        else throw exc;
      }
    }
  }
}

try {
  await rm(DEST, { recursive: true, force: true });
  await mirror(FOLDER_ID, DEST_ROOT);
  console.log("mirrored", FOLDER_ID, "->", DEST_ROOT,
    `(${folders + 1} folders, ${docs} docs, +metadata.opf)`);
} catch (exc) {
  if (exc instanceof EloError) console.log("mirror failed:", exc.message);
  else throw exc;
} finally {
  elo.close();
}
