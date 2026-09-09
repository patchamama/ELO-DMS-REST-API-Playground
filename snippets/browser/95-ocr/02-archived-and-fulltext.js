// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Get the text of a document already in the archive
// category: OCR & text extraction
// id:       ocr.archived

const elo = await connect();
const ALL = "449304431574384639";

const res = await elo.call("findFirstSords", {
  findInfo: { findByType: { typeMin: 254, typeMax: 998 } },
  max: 1, sordZ: { bset: ALL },
});
const docs = res.sords || [];
if (res.searchId) await elo.call("findClose", { searchId: res.searchId });

if (!docs.length) {
  console.log("no documents in this archive - nothing to OCR");
} else {
  const objId = String(docs[0].id);
  console.log(`working on document ${objId}  "${docs[0].name}"`);
  try {
    const ocr = await elo.call("processOcr", {
      ocrInfo: { recognizeFile: { objId, outputFormat: 0, pageNo: -1 } },
    });
    const text = ((ocr.recognizeFile || {}).text || "").trim();
    console.log("OCR text (first 120 chars):", text.slice(0, 120) || "(empty)");
  } catch (exc) {
    console.log("processOcr failed:", exc.message);
  }
}
