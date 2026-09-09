// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Send a document to the Textreader and get its text
// category: Testing lab
// id:       lab.extract-text

const elo = await connect();
const objId = "4711";

const res = await elo.call("processOcr", {
  ocrInfo: { recognizeFile: { objId, outputFormat: 0, pageNo: -1 } },
});
const rf = res.recognizeFile || {};
if (res.exception) console.error("OCR error:", res.exception);
else { console.log("OCR text:"); console.log((rf.text || "").trim()); }
