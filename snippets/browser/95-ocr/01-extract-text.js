// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    OCR a file and show the recognised text
// category: OCR & text extraction
// id:       ocr.extract

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = "http://localhost:9090/ix-Repository1";
const ELO_USER = "Administrator";
const ELO_PASS = "elo";

// base64 of a Uint8Array (btoa needs a binary string)
const toB64 = (u8) => {
  let s = "";
  for (const b of u8) s += String.fromCharCode(b);
  return btoa(s);
};

// "Choose file" above picks a real scan; without it a tiny built-in invoice
// is sent so the snippet is self-contained.
const picked = attachment();
let name;
let ext;
let b64;
if (picked) {
  name = picked.name;
  ext = name.includes(".") ? name.split(".").pop().toLowerCase() : "txt";
  b64 = toB64(picked.bytes);
} else {
  name = "invoice.txt";
  ext = "txt";
  b64 = toB64(
    new TextEncoder().encode(
      "INVOICE 2026-0042\nAcme GmbH\nNet:   1,234.56 EUR\nVAT 19%: 234.57 EUR\nTotal: 1,469.13 EUR\n"
    )
  );
}
console.log(`sending ${name}  (contentType=${ext})`);

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
try {
  const res = await elo.call("processOcr", {
    ocrInfo: {
      recognizeFile: { imageData: { data: b64, contentType: ext }, outputFormat: 0, pageNo: -1 },
    },
  });
  const rf = res.recognizeFile;
  if (!rf || res.exception) console.log("OCR returned no text:", res.exception || "(empty)");
  else {
    console.log("--- recognised text ---");
    console.log((rf.text || "").trim());
  }
} catch (exc) {
  console.log("OCR call failed:", exc.message);
}
