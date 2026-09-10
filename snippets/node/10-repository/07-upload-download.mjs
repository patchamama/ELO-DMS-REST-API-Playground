// import the shared client:  import { connect } from "elo-playground";
// topic:    Upload and download a document (write)
// category: Repository & objects
// id:       repository.upload-download

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

const parentId = 1;
const payload = Buffer.from("hello from the playground\n");

// 1) a Sord template for the new document
const sord = (await elo.call("createDoc", {
  parentId, maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
sord.name = "pg-hello.txt";

// 2) ask for an upload URL
const doc = await elo.call("checkinDocBegin", { sord, document: { docs: [{ ext: "txt" }] } });

// 3) POST the bytes and record the server's upload token
doc.docs[0].uploadResult = await elo.upload(doc.docs[0].url, payload);

// 4) commit
const res = await elo.call("checkinDocEnd", {
  sord, document: doc, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
});
const docId = String(res.objId);
console.log("uploaded doc id:", docId);

try {
  // --- read it back ---
  const info = await elo.call("checkoutDoc", {
    objId: docId, editInfoZ: { bset: "320", sordZ: { bset: "0" } },
  });
  console.log("round-trip content:", (await elo.download(info.document.docs[0].url)).trim());
} catch (exc) {
  if (exc instanceof EloError) console.log("download failed:", exc.message);
  else throw exc;
} finally {
  for (const step of [false, true]) {
    try {
      await elo.call("deleteSord", { objId: docId, parentId: "1", deleteOptions: { deleteFinally: step } });
    } catch (e) { /* best effort */ }
  }
  elo.close();
}
