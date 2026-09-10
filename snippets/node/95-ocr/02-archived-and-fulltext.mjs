// import the shared client:  import { connect } from "elo-playground";
// topic:    Get the text of a document that is in the archive
// category: OCR & text extraction
// id:       ocr.archived

import { connect, EloError, attachment } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

// --- provision: upload a document ("Choose file" above, else a sample) ---
const picked = attachment();
const docName = picked ? picked.name : "pg-ocr-doc.txt";
const body = picked
  ? Buffer.from(picked.bytes)
  : Buffer.from("INVOICE 2026-0042\nAcme GmbH\nTotal: 1,469.13 EUR\n", "utf-8");
const ext = docName.includes(".") ? docName.split(".").pop().toLowerCase() : "txt";
const sord = (await elo.call("createDoc", {
  parentId: 1, maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
sord.name = docName;
const doc = await elo.call("checkinDocBegin", { sord, document: { docs: [{ ext }] } });
doc.docs[0].uploadResult = await elo.upload(doc.docs[0].url, body);
const objId = String((await elo.call("checkinDocEnd", {
  sord, document: doc, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
})).objId);
console.log("uploaded doc", objId);

try {
  // 1) OCR it now
  try {
    const ocr = await elo.call("processOcr", {
      ocrInfo: { recognizeFile: { objId, outputFormat: 0, pageNo: -1 } },
    });
    const text = (((ocr.recognizeFile || {}).text) || "").split(/\s+/).join(" ").trim();
    console.log("OCR text (first 120):", text.slice(0, 120) || "(empty)");
  } catch (exc) {
    if (exc instanceof EloError) console.log("processOcr failed:", exc.message);
    else throw exc;
  }

  // 2) or read the already-extracted fulltext
  const info = await elo.call("checkoutDoc", {
    objId, editInfoZ: { bset: "320", sordZ: { bset: "0" } },
  });
  const docs = ((info.document || {}).docs) || [];
  const ftc = docs.length ? docs[0].fulltextContent : null;
  console.log(
    "fulltext index text :",
    (ftc && typeof ftc === "object" ? ftc.data : null) || "(not indexed on this archive)"
  );
} finally {
  for (const step of [false, true]) {
    try {
      await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: step } });
    } catch (e) { /* best effort */ }
  }
  console.log("cleaned up");
  elo.close();
}
