// import the shared client:  import { connect } from "elo-playground";
// topic:    Create a public share link for a document
// category: Testing lab
// id:       lab.share-link

import { connect, EloError } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const ALL = "449304431574384639";

// --- provision: upload a throwaway document ---
const body = Buffer.from("public share demo\n", "utf-8");
const sord = (await elo.call("createDoc", {
  parentId: 1, maskId: 0, editInfoZ: { bset: "1", sordZ: { bset: ALL } },
})).sord;
sord.name = "pg-share.txt";
const doc = await elo.call("checkinDocBegin", { sord, document: { docs: [{ ext: "txt" }] } });
doc.docs[0].uploadResult = await elo.upload(doc.docs[0].url, body);
const objId = String((await elo.call("checkinDocEnd", {
  sord, document: doc, sordZ: { bset: ALL }, unlockZ: { bset: "1" },
})).objId);
console.log("uploaded doc", objId);

try {
  // 1) mint a public download link
  const pd = await elo.call("insertPublicDownload", {
    opts: { objId, remaining: 5, fileNameFromSordName: true },
  });
  console.log("share url :", pd.url);
  console.log("remaining :", pd.remaining);

  // 2) list the links for this object
  const links = await elo.call("getPublicDownloads", { opts: { objId } });
  console.log("links now :", links.length);

  // 3) revoke them
  await elo.call("terminatePublicDownloadUrls", { opts: { objId } });
  console.log("after revoke:", (await elo.call("getPublicDownloads", { opts: { objId } })).length);
} catch (exc) {
  if (exc instanceof EloError) console.log("share-link operation failed:", exc.message);
  else throw exc;
} finally {
  for (const step of [false, true]) {
    try {
      await elo.call("deleteSord", { objId, parentId: "1", deleteOptions: { deleteFinally: step } });
    } catch (e) { /* best effort */ }
  }
  console.log("cleaned up");
  elo.close();
}
