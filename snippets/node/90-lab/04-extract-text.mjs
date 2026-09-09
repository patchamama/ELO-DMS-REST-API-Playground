// import the shared client:  import { connect } from "elo-playground";
// topic:    Send a document to the Textreader and get its text
// category: Testing lab
// id:       lab.extract-text

import { connect } from "elo-playground";

const elo = await connect();

const objId = "4711"; // an archived document to run OCR on

const res = await elo.call("processOcr", {
  ocrInfo: {
    recognizeFile: {
      objId,           // ...OR: imageData: { data: <base64>, contentType: "application/pdf" }
      outputFormat: 0, // OcrInfoC.TEXT -> plain text
      pageNo: -1,      // -1 = every page
    },
  },
});

const rf = res.recognizeFile || {};
if (res.exception) console.error("OCR error:", res.exception);
else {
  console.log("OCR text:");
  console.log((rf.text || "").trim());
}
