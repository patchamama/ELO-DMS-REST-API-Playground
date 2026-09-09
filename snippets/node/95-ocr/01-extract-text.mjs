// import the shared client:  import { connect } from "elo-playground";
// topic:    OCR a file and show the recognised text
// category: OCR & text extraction
// id:       ocr.extract

import { connect, EloError } from "elo-playground";

const elo = await connect();

// A tiny "invoice" as plain-text bytes so this snippet is self-contained.
// For a real scan: read examples/invoices/invoice-2026-0042-acme.pdf and
// set contentType to "pdf".
const payload = Buffer.from(
  "INVOICE 2026-0042\n" +
    "Acme GmbH\n" +
    "Net:   1,234.56 EUR\n" +
    "VAT 19%: 234.57 EUR\n" +
    "Total: 1,469.13 EUR\n",
  "utf-8"
);

try {
  const res = await elo.call("processOcr", {
    ocrInfo: {
      recognizeFile: {
        imageData: { data: payload.toString("base64"), contentType: "txt" },
        outputFormat: 0, // OcrInfoC.TEXT
        pageNo: -1, // every page
      },
    },
  });
  const rf = res.recognizeFile;
  if (!rf || res.exception) {
    console.log("OCR returned no text:", res.exception || "(empty result)");
  } else {
    console.log("--- recognised text ---");
    console.log((rf.text || "").trim());
  }
} catch (exc) {
  if (exc instanceof EloError) console.log("OCR call failed:", exc.message);
  else throw exc;
} finally {
  elo.close();
}
