// import the shared client:  import { connect } from "elo-playground";
// topic:    OCR a file and show the recognised text
// category: OCR & text extraction
// id:       ocr.extract

import { connect, EloError, attachment } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "";

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

// "Choose file" above picks a real scan; without it a tiny built-in invoice
// is sent so the snippet is self-contained.
const picked = attachment();
let name;
let ext;
let data;
if (picked) {
  name = picked.name;
  ext = name.includes(".") ? name.split(".").pop().toLowerCase() : "txt";
  data = Buffer.from(picked.bytes);
} else {
  name = "invoice.txt";
  ext = "txt";
  data = Buffer.from(
    "INVOICE 2026-0042\nAcme GmbH\nNet:   1,234.56 EUR\nVAT 19%: 234.57 EUR\nTotal: 1,469.13 EUR\n",
    "utf-8"
  );
}
console.log(`sending ${name}  (${data.length} bytes, contentType=${ext})`);

try {
  const res = await elo.call("processOcr", {
    ocrInfo: {
      recognizeFile: {
        imageData: { data: data.toString("base64"), contentType: ext },
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
