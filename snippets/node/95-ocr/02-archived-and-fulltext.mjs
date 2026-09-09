// import the shared client:  import { connect } from "elo-playground";
// topic:    Get the text of a document already in the archive
// category: OCR & text extraction
// id:       ocr.archived

import { connect, EloError } from "elo-playground";

const elo = await connect();
const ALL = "449304431574384639";

try {
  // 1) find the first document in the archive to work on
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

    // 2) OCR it now
    try {
      const ocr = await elo.call("processOcr", {
        ocrInfo: { recognizeFile: { objId, outputFormat: 0, pageNo: -1 } },
      });
      const text = ((ocr.recognizeFile || {}).text || "").trim();
      console.log("OCR text (first 120 chars):", text.slice(0, 120) || "(empty)");
    } catch (exc) {
      if (exc instanceof EloError) console.log("processOcr failed:", exc.message);
      else throw exc;
    }

    // 3) or read the text the fulltext pipeline already extracted
    const doc = await elo.call("checkoutDoc", {
      objId, editInfoZ: { bset: "1", sordZ: { bset: "0" } },
    });
    const versions = ((doc.document || {}).docs) || [];
    const ftc = versions.length ? versions[0].fulltextContent : null;
    console.log(
      "fulltext index text     :",
      (ftc && typeof ftc === "object" ? ftc.data : null) || "(not indexed on this archive)"
    );
  }
} finally {
  elo.close();
}
