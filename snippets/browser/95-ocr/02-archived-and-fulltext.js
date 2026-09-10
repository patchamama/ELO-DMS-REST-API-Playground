// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Get the text of a document that is in the archive
// category: OCR & text extraction
// id:       ocr.archived

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

// Uploading a document is not available from the browser (the connector is
// on another origin). Run this one from the Python or Node tab; the browser
// client would throw on elo.upload().
const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
try {
  const ocr = await elo.call("processOcr", {
    ocrInfo: { recognizeFile: { objId: "5001", outputFormat: 0, pageNo: -1 } },
  });
  const text = (((ocr.recognizeFile || {}).text) || "").split(/\s+/).join(" ").trim();
  console.log("OCR text (first 120):", text.slice(0, 120) || "(empty)");
} catch (exc) {
  console.log("processOcr failed:", exc.message);
}
