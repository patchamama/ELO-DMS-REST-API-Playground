// import the shared client:  import { connect } from "elo-playground";
// topic:    Find a Business Solution config document
// category: Business Solutions
// id:       business-solutions.find-config

import { connect } from "elo-playground";

// --- local ELO test box (override with ELOPG_* env vars or a .env) ---
const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user
const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password

const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });

// 1) find "*.config.json" documents (type >= 254 is a document)
const hits = await elo.findAll("findFirstSords", "findNextSords", "sords", {
  findInfo: { findByIndex: { name: "*.config.json" } },
  max: 50,
  sordZ: { bset: "449304431574384639" },
});
const doc = hits.find((s) => Number(s.type || 0) >= 254);
console.log("config document:", doc.name, "id", doc.id);

// 2) check it out for an authenticated download URL
const info = await elo.call("checkoutDoc", {
  objId: String(doc.id),
  editInfoZ: { bset: "320", sordZ: { bset: "0" } },
});
const url = (info.document?.docs || [{}])[0].url;

// 3) download and parse
const cfg = JSON.parse(await elo.download(url, { maxBytes: 100000 }));
console.log("top-level keys:", Object.keys(cfg).slice(0, 10));
