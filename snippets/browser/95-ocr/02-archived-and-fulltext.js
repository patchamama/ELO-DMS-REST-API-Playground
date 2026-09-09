// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Get the text of a document that is in the archive
// category: OCR & text extraction
// id:       ocr.archived

// Uploading a document is not available from the browser (the connector is
// on another origin). Run this one from the Python or Node tab; the browser
// client would throw on elo.upload().
const elo = await connect();
try {
  const ocr = await elo.call("processOcr", {
    ocrInfo: { recognizeFile: { objId: "5001", outputFormat: 0, pageNo: -1 } },
  });
  const text = (((ocr.recognizeFile || {}).text) || "").split(/\s+/).join(" ").trim();
  console.log("OCR text (first 120):", text.slice(0, 120) || "(empty)");
} catch (exc) {
  console.log("processOcr failed:", exc.message);
}
