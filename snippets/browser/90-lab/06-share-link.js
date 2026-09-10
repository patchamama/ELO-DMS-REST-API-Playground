// in a real page:  import { connect } from "./eloClient.browser.js"
// (in the playground run-sandbox, connect() is already a global)
// topic:    Create a public share link for a document
// category: Testing lab
// id:       lab.share-link

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = globalThis.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1";
const ELO_USER = globalThis.ELOPG_ELO_USER || "Administrator";
const ELO_PASS = globalThis.ELOPG_ELO_PASSWORD || "";

// Uploading a document is not available from the browser (the connector is
// on another origin). Run this one from the Python or Node tab.
const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });
const objId = "5570"; // an existing document's id

try {
  const pd = await elo.call("insertPublicDownload", {
    opts: { objId, remaining: 5, fileNameFromSordName: true },
  });
  console.log("share url :", pd.url);
  const links = await elo.call("getPublicDownloads", { opts: { objId } });
  console.log("links now :", links.length);
  await elo.call("terminatePublicDownloadUrls", { opts: { objId } });
  console.log("revoked");
} catch (exc) {
  console.log("share-link operation failed:", exc.message);
}
